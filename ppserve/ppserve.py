#!/usr/bin/env python3

import argparse
parser = argparse.ArgumentParser(description="Serve quotes and historic prices for use with PortfolioPerformance")
parser.add_argument(
    '-c-', '--default-currency', dest='default_currency', default='EUR',
    help='Default currency used for conversion.'
)
parser.add_argument(
    '--hostname', dest='hostname', default='localhost',
    help='Host name or address to bind to.'
)
parser.add_argument(
    '--port', dest='port', type=int, default=9444,
    help='Port number to use.'
)
parser.add_argument(
    '--log-level', dest='log_level', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='INFO',
    help='Log verbosity.'
)
args = parser.parse_args()

from datetime import date, timedelta
from time import sleep
from pathlib import Path
import sys
import collections
from bottle import route, run, SimpleTemplate, abort, redirect, template
from threading import Thread

from .price_sources import ArivaPriceSource
from .price_sources.securities import Bond

template_path = Path(__file__).parent/"templates"
portfolio_performance_template = SimpleTemplate(
    open(template_path/"portfolio_performance.html", 'r')
)
portfolio_performance_historical_template = SimpleTemplate(
    open(template_path/"portfolio_performance_historical.html", 'r')
)

my_bonds = {}

# Serve quote tables for Portfolio Performance
@route('/<mode>/<symbol>/<clean_or_dirty>/<currency>')
def serve_quote_table(mode, symbol, clean_or_dirty, currency):
    if symbol in my_bonds.keys():
        sec = my_bonds[symbol]
        sec.update()
    else:
        sec = ArivaPriceSource(symbol).security()
        my_bonds[symbol] = sec

    print(sec.pretty_print(target_currency=currency))

    if mode == 'quote':
        if clean_or_dirty == 'dirty':
            if type(sec) is Bond:
                # hi, lo, la = bond.dirty_high(currency), bond.dirty_low(currency), bond.dirty_last(currency)
                # FIXME: last and low currently broken (ArivaPriceSource does not support it)
                la = sec.dirty_last(currency)
                hi = la
                lo = la
            else:
                abort(500, 'Dirty prices are only available for bonds.')
        else:
            la = sec.last(currency)
            hi = la
            lo = la

        return portfolio_performance_template.render(
            symbol = symbol,
            name = sec.name,
            url = sec.url,
            date = sec.last_price_update,
            high = hi,
            low = lo,
            last = la,
            note = "All rates are {} and, if necessary, converted to {}.".format(clean_or_dirty, currency)
        )

    if mode in ['historic', 'historical']:
        if clean_or_dirty == 'dirty':
            if type(sec) == Bond:
                hist = collections.OrderedDict(sorted(sec.dirty_price_history(currency).items()))
            else:
                abort(500, 'Dirty prices are only available for bonds.')
        else:
            hist = collections.OrderedDict(sorted(sec.price_history(currency).items()))

        return portfolio_performance_historical_template.render(
            symbol = symbol,
            name = sec.name,
            url = sec.url,
            price_history = hist,
            note = "All rates are {} and, if necessary, converted to {}.".format(clean_or_dirty, currency)
        )

    abort(404, "Please specify symbol, mode, and currency correctly.")

# allow omission of the currency...
@route('/<mode>/<symbol>/<clean_or_dirty>')
def redirect_to_default_currency(mode, symbol, clean_or_dirty):
    return serve_quote_table(mode, symbol, clean_or_dirty, args.default_currency)

# ... and whether bond prices should be clean or dirty
@route('/<mode>/<symbol>')
def redirect_to_default_mode(mode, symbol):
    return serve_quote_table(mode, symbol, 'clean', args.default_currency)

def update_sec_prices(sec):
    start_date = None

    if not sec._price_history:
        start_date = date(2015,12,10)
    else:
        last_quote_date = max(sec._price_history.keys())
        if (date.today() - last_quote_date).days > 0:
            start_date = last_quote_date + timedelta(days=1)

    if start_date:
        sec.update_historic(start_date, date.today())
        sec.write_quotes()

def main():
    global my_bonds

    import logging
    import coloredlogs
    # logging.basicConfig(format='%(levelname)s: %(name)s: %(message)s', level=getattr(logging, args.log_level))
    logger = logging.getLogger('Main')
    coloredlogs.install(level=getattr(logging, args.log_level))

    logger.info('Loading manually configured securities.')
    from .my_bonds import load_my_bonds
    yaml_file = Path.home()/'.ppserve'/'my_bonds.yaml'

    try:
        my_bonds = load_my_bonds(yaml_file)
        logger.info('Found configuration in {}'.format(str(yaml_file)))
    except FileNotFoundError:
        logger.info('No my_bonds.yaml found.')

    try:
        Thread(
            target=run, name="price server",
            kwargs={'server': 'paste', 'host': args.hostname, 'port': args.port}
        ).start()

        updater_threads = []

        while True:
            # Update bond price history if needed
            for sec in my_bonds.values():
                t = Thread(
                    target=update_sec_prices,
                    name="historical price updater for {}".format(sec.symbol),
                    kwargs={'sec': sec}
                )
                updater_threads.append(t)
                t.start()

            sleep(3*3600) # wait for 3 hours

    except KeyboardInterrupt:
        sys.exit()
