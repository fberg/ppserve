# ppserve

[Portfolio Performance](https://www.portfolio-performance.info/portfolio/) is an open source Java application for tracking and managing portfolios of financial securities (e.g. stocks).
While it can fetch quotes from Yahoo Finance and some other sources, it is sometimes hard to get quotes for securities that are not stocks, for instance funds/ETFs or bonds.

This program fetches quotes and historical prices by scraping websites for the necessary info (currently only [Ariva](https://www.ariva.de/) is supported) and serving the quotes on a local web server (using `bottle`) in a format that Portfolio Performance understands (a HTML table with certain format).

`ppserve` can also be made to compute or fetch dirty prices of bonds (i.e. including accrued interest).

Once started, it listens for the following routes: `/<mode>/<symbol>/<clean_or_dirty>/<currency>`, where `<mode>` is either "quote" or "historic", `<symbol>` is the WKN or ISIN of the security, `clean_or_dirty` indicates if a bond is to be priced with or without accrued interest, and `<currency>` is the currency the price is to be converted to.
The currency and `clean_or_dirty` may be omitted (currency defaults to the argument of `--default-currency`).

## Configuration

A file `my_bonds.yaml` in `~/.ppserve/` can be used to preconfigure bonds (e.g. if some of the data is not available from the price source).
This is mostly useful for providing missing information needed for accrued interest computation.
The syntax is as follows:

```yaml
...
<symbol (WKN or ISIN)>:
  currency: <currency>
  interest_dates: <list of pairs [day, month] at which interest payments are made>
  interest_from: <starting date of interest accumulation>
  interest_rate: <the bond's coupon>
  maturity: <date of maturity>
...
```
Date and list formatting is standard YAML.

## Installation

Installation is done by running `python setup.py install --user` (skip `--user` to install system-wide).
This installs a binary called `ppserve`.
Check `ppserve -h` to see command line options.

## Dependencies

[`BeautifulSoup`](https://www.crummy.com/software/BeautifulSoup/) for scraping, [`bottle`](http://bottlepy.org/docs/dev/) for serving HTML, [`coloredlogs`](https://pypi.org/project/coloredlogs/) for fancy output, [`CurrencyConverter`](https://pypi.org/project/CurrencyConverter/) for currency conversion, and [`PyYAML`](https://pyyaml.org/) for config file parsing.

## Disclaimer

By its nature (i.e. scraping sites that may change at any moment), this program is rather sketchy and will probably break every once in a while.
