from datetime import date

# from forex_python.converter import CurrencyRates # too slow
from currency_converter import CurrencyConverter

currency_rates = CurrencyConverter(
    'http://www.ecb.int/stats/eurofxref/eurofxref-hist.zip',
    fallback_on_missing_rate=True,
    fallback_on_wrong_date=True
)

# computes exchange rate between currencies
def currex(currency, target_currency=None, date_=None):
    if currency == target_currency or target_currency is None:
        return 1
    else:
        return currency_rates.convert(1, currency, target_currency, date=date_)

# decorator to handle currency conversion
def currency_aware(f):
    def f_currency(sec, target_currency=None):
        val = f(sec)
        if val is None:
            return None
        if type(val) == dict:
            # if the type is dict, the keys need to be the target date for the currency conversion
            new_val = {d: v * currex(sec.currency, target_currency, date_=d) for (d,v) in val.items()}
        else:
            new_val = val * currex(sec.currency, target_currency, date_=date.today())
        return new_val
    return f_currency
