from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
import csv
import collections
# import os
import logging
from pathlib import Path

from .util import currex, currency_aware

class Security:
    """
    General class representing a financial security. Provides methods for
    currency conversion and for reading and writing quotes to disk.
    """

    def __init__(self, symbol, read_quotes=True):
        self.symbol = symbol

        self.url = None
        self.update_hook = None
        self.update_hook_historic = None
        self.name = None
        self.currency = None
        self._last = None
        self._high = None
        self._low = None
        self._price_history = {}
        self.last_price_update = None

        if read_quotes:
            self.read_quotes()

        self.logger = logging.getLogger(self.symbol)

    def update(self):
        if self.update_hook is None:
            raise Exception('update_hook was not given')
        else:
            self.update_from_dict(self.update_hook())

    def update_from_dict(self, data, overwrite=True):
        nothing_new = True

        for key, value in data.items():
            if hasattr(self, key):
                if getattr(self, key) == value:
                    logfn = lambda x: None
                else:
                    if not overwrite:
                        self.logger.debug(
                            'Got {} = {} (was {}), but not overwriting it.'.format(
                                key, repr(value), repr(getattr(self, key))
                            )
                        )
                    logfn = self.logger.debug
                    nothing_new = False
                logfn('Updating {} = {} (was {})'.format(key, repr(value), repr(getattr(self, key))))
                setattr(self, key, value)

        if nothing_new:
            self.logger.debug('Nothing to update')

    def update_historic(self, start_date, end_date):
        if self.update_hook_historic is None:
            raise Exception('update_hook_historic was not given')
        else:
            self.update_historic_from_dict(self.update_hook_historic(start_date, end_date))

    def update_historic_from_dict(self, data, overwrite=True):
        for d, quote in data.items():
            if d in self._price_history.keys():
                if overwrite and self._price_history[d] != quote:
                    self.logger.debug("Overwriting existing quote for {}: {} (was {})".format(d.strftime('%Y-%m-%d'), quote, self._price_history[d]))
                    self._price_history[d] = quote
            else:
                self.logger.debug("Found historical quote: {}: {}".format(d.strftime('%Y-%m-%d'), quote))
                self._price_history[d] = quote

    @currency_aware
    def last(self): return self._last

    @currency_aware
    def high(self): return self._high

    @currency_aware
    def low(self): return self._low

    @currency_aware
    def price_history(self): return self._price_history

    @property
    def _quotes_path(self):
        return Path(__file__).parent/'quotes'/(self.symbol + '.quotes')

    def write_quotes(self, path=None):
        if path is None:
            path = self._quotes_path

        with open(path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = ["date","last"])
            writer.writeheader()

            for d,quote in collections.OrderedDict(sorted(self._price_history.items())).items():
                writer.writerow({"date": d, "last": quote})

    def read_quotes(self, path=None):
        if path is None:
            path = self._quotes_path

        try:
            with open(path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self._price_history[datetime.strptime(row["date"], '%Y-%m-%d').date()] = float(row["last"])
        except FileNotFoundError:
            self._price_history = {}

    def pretty_print(self, target_currency=None):
        from termcolor import colored
        return ("{} " + colored("{}", 'blue', attrs=['bold']) + " (" + colored("{}", attrs=['bold']) + ") Last: " + colored("{}", 'red', attrs=['bold']) + " {}{}").format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            self.symbol,
            self.name,
            self.last(),
            self.currency,
            ', Exchange rate: {}'.format(round(1/currex(self.currency, target_currency),4)) if self.currency != target_currency else '',
        )
