const fs = require("fs");
const puppeteer = require("puppeteer");
const { cli } = require("cli-ux");
const crypto = require("crypto");
const cheerio = require("cheerio");
const path = require("path");
const { assert } = require("console");
const sandman = require("../utils/sandman");
const { spawnSync } = require("child_process");
const fsExtra = require("fs-extra");

class BelegExporter {
  async run() {
    this.logger = console;
    try {
      await this.handleMigros();
      await this.handleCoop();
    } catch (err) {
      this.logger.error(err);

      let readyToFinish = false;
      while (!readyToFinish) {
        readyToFinish = await cli.confirm("Ready To Exit? (y/n)");
      }
      await this.driver.close();
      await this.browser.close();
    }
    return 0;
  }

  async handleMigros() {
    await this.initializeBrowser();
    this.logger.log("Login & navigate to the Migros page to download.");

    let targetPage = "https://cumulus.migros.ch/de/konto/kassenbons.html";
    await this.driver.goto(targetPage);
    let loggedIn = false;
    while (!loggedIn) {
      loggedIn = await cli.confirm("Login finished? (y/n)");
    }
    await this.driver.goto(targetPage);
    // adjust the date
    let minDate = await this.driver.$eval("#ref-dateFrom", (el) => {
      return el.getAttribute("min");
    });
    let maxDate = await this.driver.$eval("#ref-dateTo", (el) => {
      return el.getAttribute("max");
    });
    // run the update
    let actualTargetPage = targetPage + "?period=" + minDate + "_" + maxDate;
    await this.driver.goto(actualTargetPage);
    // await this.driver.click(".ui-js-date-submit [name='formsubmit']");

    // now, finally, start iterating through the resulting pagination
    let hasMorePages = true;
    let numExports = 0;
    const download_path_tmp = path.join(__dirname, "..", "tmp-downloads");
    const download_path = path.join(__dirname, "..", "downloads", "migros");

    if (!fs.existsSync(download_path)) {
      fs.mkdirSync(download_path, { recursive: true });
    }
    if (!fs.existsSync(download_path_tmp)) {
      fs.mkdirSync(download_path_tmp, { recursive: true });
    }
    await fsExtra.emptyDirSync(download_path_tmp);

    while (hasMorePages) {
      // download the CSV for this page
      await this.driver.client().send("Page.setDownloadBehavior", {
        behavior: "allow",
        downloadPath: download_path_tmp,
      });
      await sandman.sleep(1000);
      // first, check all
      await this.driver.click("input[name='checkbox-all']");
      // then, actually download
      await this.driver.click(
        "input.btn[value='Excel-Liste (CSV) exportieren']"
      );
      await sandman.sleep(2000);

      // move the downloaded file
      let files = fs.readdirSync(download_path_tmp);
      assert(files.length === 1);
      files.forEach((file) => {
        fs.renameSync(
          path.join(download_path_tmp, file),
          path.join(download_path, "recipes-" + numExports + ".csv")
        );
      });

      numExports += 1;
      // check whether there are more
      // go to next page
      hasMorePages = await this.driver
        .$eval("ul.pagination.is-cumulus a.page.next", (el) => {
          el.click();
          return true;
        })
        .catch(() => false);
    }

    this.logger.log("Exported " + numExports + " CSV files");

    await this.driver.close();
    await this.browser.close();
  }

  async handleCoop() {
    await this.initializeBrowser();
    this.logger.log("Login & navigate to the Coop page to download.");

    let targetPage = "https://www.coop.ch/de/my-orders";
    await this.driver.goto(targetPage);
    let loggedIn = false;
    while (!loggedIn) {
      loggedIn = await cli.confirm("Login finished? (y/n)");
    }
    await this.driver.goto(targetPage);
    await sandman.sleep(2000);

    // now, finally, start iterating through the resulting pagination
    let hasMorePages = true;
    let numExports = 0;
    let pageNr = 0;
    const download_path_tmp = path.join(__dirname, "..", "tmp-downloads");
    const download_path = path.join(__dirname, "..", "downloads", "coop");
    if (!fs.existsSync(download_path)) {
      fs.mkdirSync(download_path, { recursive: true });
    }
    if (!fs.existsSync(download_path_tmp)) {
      fs.mkdirSync(download_path_tmp, { recursive: true });
    }
    await fsExtra.emptyDirSync(download_path_tmp);

    await this.driver._client.send("Page.setDownloadBehavior", {
      behavior: "allow",
      downloadPath: download_path_tmp,
    });

    while (hasMorePages) {
      // download the PDFs for this page
      let pdfLinks = await this.driver.$$(
        "div.order__item-link-wrapper i.icon-document"
      );
      this.logger.log("Found " + pdfLinks.length + " links on page " + pageNr);

      let pdfLinkIdx = 0;
      while (pdfLinkIdx < pdfLinks.length) {
        try {
          await pdfLinks[pdfLinkIdx].click();
        } catch (e) {
          this.logger.warn(e);
          await pdfLinks[pdfLinkIdx].evaluate((el) => el.click());
        }
        // download the CSV for this page
        await sandman.sleep(2000);

        // move the downloaded file
        let files = fs.readdirSync(download_path_tmp);
        assert(files.length === 1);
        files.forEach(async (file) => {
          // const {stdout, stderr} = await exec("/usr/bin/env python " + );
          const out = spawnSync(
            "python",
            [
              path.join(__dirname, "..", "parse-coop-recipe-pdf-to-csv.py"),
              path.join(download_path_tmp, file),
            ],
            { encoding: "utf-8" }
          );

          await sandman.sleep(500);

          if (out.stderr) {
            this.logger.error(out.stderr);
          }

          fs.renameSync(
            out.stdout.trim(),
            path.join(download_path, path.basename(out.stdout.trim()))
          );

          fs.rmSync(path.join(download_path_tmp, file));
        });
        await sandman.sleep(2000);

        pdfLinkIdx += 1;
        numExports += 1;
      }

      // check whether there are more
      // go to next page
      hasMorePages = await this.driver
        .$eval("div.productListPageNav a.pagination__next", (el) => {
          el.click();
          return true;
        })
        .catch(() => false);
      pageNr += 1;
      await sandman.sleep(2000);
    }

    this.logger.log("Exported " + numExports + " CSV files");

    await this.driver.close();
    await this.browser.close();
  }

  /**
   * Open a new page/tab
   *
   * @returns {void} void
   */
  async openNewPage() {
    try {
      this.driver = await this.browser.newPage();
    } catch (error) {
      this.logger.error(error);

      return;
    }
    this.driver.setViewport({
      height: 0,
      width: 0,
    });
  }

  /**
   * Set up the browser
   *
   * @returns {void} void
   */
  async initializeBrowser() {
    this.browser = await puppeteer.launch({
      headless: false,
      userDataDir: "./user_data",
    });
    await this.openNewPage();
  }
}

let iE = new BelegExporter();
iE.run();
