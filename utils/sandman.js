class Sandman {
  /**
   * Sleep for a random amount of time
   *
   * @param {double} maximum The maximum sleep time in milliseconds
   */
  async randomSleep(maximum = 10_000) {
    await this.sleep(maximum * Math.random())
  }

  /**
   * Sleep for a certain time, but only if you have time to `await` it
   *
   * @param {double} millis Millisecond time to sleep
   * @returns {Promise} to sleep. Just like we did. In the end still read a book under the bed sheets.
   */
  sleep(millis) {
    // eslint-disable-next-line no-promise-executor-return
    return new Promise(resolve => setTimeout(resolve, millis))
  }
}

module.exports = new Sandman()
