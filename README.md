# ppserve

[Portfolio Performance](https://www.portfolio-performance.info/portfolio/) is an open source Java application for tracking and managing portfolios of financial securities (e.g. stocks).
While it can fetch quotes from Yahoo Finance and some other sources, it is sometimes hard to get quotes for securities that are not stocks, for instance funds/ETFs or bonds.

This program fetches quotes and historical prices by scraping websites for the necessary info (currently only [Ariva](https://www.ariva.de/) is supported) and serving the quotes on a local web server (using `bottle`) in a format that Portfolio Performance understands (a HTML table with certain format).

`ppserve` can also be made to compute or fetch dirty prices of bonds (i.e. including accrued interest).

Once started, it listens for the following routes: `/<mode>/<symbol>/<clean_or_dirty>/<currency>`, where `<mode>` is either "quote" or "historic", `<symbol>` is the WKN or ISIN of the security, `clean_or_dirty` indicates if a bond is to be priced with or without accrued interest, and `<currency>` is the currency the price is to be converted to.
The currency and `clean_or_dirty` may be omitted (currency defaults to the argument of `--default-currency`).

# Dependencies

[`BeautifulSoup`](https://www.crummy.com/software/BeautifulSoup/) for scraping, [`bottle`](http://bottlepy.org/docs/dev/) for serving HTML, [`coloredlogs`](https://pypi.org/project/coloredlogs/) for fancy output.

# Disclaimer

By its nature (i.e. scraping sites that may change at any moment), this program is rather sketchy and will probably break every once in a while.
