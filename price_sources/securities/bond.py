from datetime import date
from dateutil.relativedelta import relativedelta
from math import floor

from .security import Security
from .util import currency_aware

class Bond(Security):

    def __init__(self, symbol, read_quotes=True):
        Security.__init__(self, symbol, read_quotes)

        self.interest_from = None
        self.maturity = None
        self.interest_dates = None
        self.interest_rate = None

        self._accrued_interest_fetched = None

    def __repr__(self):
        return '<Bond: symbol {}>'.format(self.symbol)

    def accrued_interest(self, target_date=None):
        """
        Returns the bond's accrued interest at target_date if there is enough information
        to compute it (or a fetched value is available).
        """
        if target_date is None:
            target_date = date.today()

        if target_date == date.today and self._accrued_interest_fetched is not None:
                return self._accrued_interest_fetched

        if (self.maturity is not None) and (self.maturity < target_date):
            return 0

        if (self.interest_dates is not None) and (self.interest_rate is not None):
            # interest_dates = [(int(d.split('.')[0]), int(d.split('.')[1])) for d in self.interest_dates]

            # find the date of the next interest payment
            next_date = None

            # look for dates in the same year as target_date
            for date_ in sorted((date(target_date.year, m, d) for d,m in self.interest_dates)):
                if target_date <= date_:
                    next_date = date_
                    break

            # look for the earliest interest date in the next year
            if next_date is None:
                next_date = min([date(target_date.year + 1, month, day) for day, month in self.interest_dates])

            computed_interest = (
                (next_date - (next_date + relativedelta(months=-floor(12/len(self.interest_dates))))).days
                - (next_date - target_date).days
            ) * self.interest_rate/365

            return computed_interest

        raise ValueError('Not enough information to compute accrued interest for {} at date {}.'.format(self.symbol, target_date))

    @currency_aware
    def dirty_high(self):
        if not self.high(): return None
        return (self.high() + self.accrued_interest())

    @currency_aware
    def dirty_low(self):
        if not self.low(): return None
        return (self.low() + self.accrued_interest())

    @currency_aware
    def dirty_last(self):
        if not self.last(): return None
        return (self.last() + self.accrued_interest())

    @currency_aware
    def dirty_price_history(self, target_currency=None):
        return {
            d: (quote + self.accrued_interest(target_date=d)) for d, quote in self._price_history.items()
        }

    @property
    def current_yield(self):
        if self._last and self.interest_rate:
            if self.maturity and (date.today() > self.maturity):
                return 0
            return self.interest_rate / self._last

    def pretty_print(self, target_currency=None):
        from termcolor import colored
        return (Security.pretty_print(self, target_currency=target_currency) + ", Dirty: " + colored("{}", 'red', attrs=['bold']) + ", Interest: {}, CY: {:.2%}").format(
            round(self.dirty_last(target_currency),3),
            round(self.accrued_interest(),3),
            self.current_yield
        )
