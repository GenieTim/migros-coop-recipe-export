# migros-coop-recipe-export

A series of simple scripts to export all bills available from Coop and Migros websites.

## Setup

```bash
git clone git@github.com:GenieTim/migros-coop-recipe-export.git
cd ./migros-coop-recipe-export
yarn
python -m pip install -r requirements.txt
```

## How to use

There are a few scripts, that partially work together.

- ./bin/run.js: use `node bin/run.js` – this script will open a browser, ask you to login (enter `y` in the command line after doing so) and then download all your bills found on the Migros and afterwards the Coop website to a new folder `downloads`
- ./parse-coop-recipe-pdf-to-csv.py: use `python parse-coop-recipe-pdf-to-csv.py {pdf-recipe-file}` – this script will be called by `bin/run.js` already, but you can also use it standalone. What it does is to parse the PDF file and translate it into a nice CSV tabular data file
- ./combine-all-by-month.py: use `python combine-all-by-month.py` – this script will read all the csv files stored in the

## Disclaimer

Use on your own risk.
Check the LICENSE: I will not take any responsibility for anything you do with this software.
