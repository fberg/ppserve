import locale
import re
import calendar
from math import floor
import urllib.request
from bs4 import BeautifulSoup as BS
import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from .pricesource import PriceSource
from ..securities import *

class ArivaPriceSource(PriceSource):
    def __init__(self, symbol):
        self.name = 'Ariva'
        PriceSource.__init__(self, symbol)

    def make_url(self):
        # User agent to use for the request. Not sure if it is necessary to pretend to be someone else.
        headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'}

        try:
            # We need to find out where Ariva redirects us to later build other URLs
            req = urllib.request.Request("http://www.ariva.de/{}".format(self.symbol), headers=headers)
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            self.logger.error('Could not find symbol {} on Ariva.'.format(self.symbol))
            raise e

        # Try to find out the security type.
        soup = BS(response.read().decode('utf-8'), 'lxml')
        security_type = soup.find('div', class_='verlauf snapshotInfo').find(text=re.compile('Typ:')).string.split(':')[1].strip()

        sec_types = {
            'Aktie': Stock,
            'ETF': ETF,
            'Fonds': ETF, # TODO: this is mostly a hack to accomodate A12GVR
            'Zertifikat': Derivative,
            'Anleihe': Bond
        }

        if security_type in sec_types.keys():
            self.sec_type = sec_types[security_type]
        if not self.sec_type:
            self.logger.warning('Could not determine security type.')

        exchange_ids = {
            Stock: 1, # Frankfurt
            ETF: 1,
            Bond: 1,
            Derivative: 39 # Frankfurt Zertifikate
        }

        # The url contains the exchange to use.
        # We make it depend on the security type.
        return urllib.request.Request(response.url + '?boerse_id={}'.format(exchange_ids[self.sec_type]), headers=headers)

    def fetch_info(self):
        self.logger.info('Fetching info using {}.'.format(self.name))
        locale.setlocale(locale.LC_NUMERIC, "de_DE.UTF-8")

        soup = self.fetch_site()
        info = {}
        info['url'] = self.url_or_request

        def _find_ariva_td(label):
            try:
                # the '\s' selects white space, so we only get entries that exactly match the label name
                # e.g. 'Kupon' does not match 'Kuponart'
                return soup.find('td', text=re.compile(label + '\s')).find_next_sibling('td').contents[0].strip()
            except AttributeError:
                self.logger.warning("Couldn't find label '{}' on the Ariva site".format(label))

        info['name'] = soup.find('h1').find(itemprop='name').contents[0].strip()

        table = soup.find('table', class_='line')
        if table.find('span', itemprop='price') is not None:
            info['_last'] = locale.atof(table.find('span', itemprop='price').contents[0])

        curr_span = table.find('span', itemprop='pricecurrency')
        if curr_span is None:
            info['currency'] = _find_ariva_td("Währung")
        else:
            curr = curr_span.contents[0]
            if curr == '$':
                info['currency'] = 'USD'
            if curr == '€':
                info['currency'] = 'EUR'

        if self.sec_type == Bond:
            if _find_ariva_td("Kupon") is not None:
                # we don't use locale.atof here, since Ariva uses the decimal point here...
                info['interest_rate'] = float(_find_ariva_td("Kupon").replace('%','').strip())

            if _find_ariva_td("Stückzinsen") is not None:
                info['_accrued_interest_fetched'] = locale.atof(_find_ariva_td("Stückzinsen").replace('%','').strip())

            if _find_ariva_td("Zinslauf ab") is not None:
                info['interest_from'] = datetime.strptime(_find_ariva_td("Zinslauf ab"), '%d.%m.%Y').date()

            if _find_ariva_td("Fälligkeit") is not None:
                if _find_ariva_td("Fälligkeit") == 'unbefristet':
                    info['maturity'] = None
                else:
                    info['maturity'] = datetime.strptime(_find_ariva_td("Fälligkeit"), '%d.%m.%Y').date()

            period = _find_ariva_td("Kuponperiode")
            if period is not None:
                num_interest_dates = None
                if period == 'Jahr':
                    num_interest_dates = 1
                if period == 'Halbjahr':
                    num_interest_dates = 2
                if period == 'Vierteljahr':
                    num_interest_dates = 4
                # UNSURE: are there more?

            if period is not None and 'interest_from' in info.keys():
                info['interest_dates'] = [
                    [_d.day,_d.month]
                    for _d in [info['interest_from'] + relativedelta(months =+ floor(12*k/num_interest_dates)) for k in range(num_interest_dates)]
                ]

        info['last_price_update'] = date.today() # TODO: make this be the actual last price date

        return info

    def fetch_historic_quotes(self, start_date, end_date):
        self.logger.info('Fetching historic quotes using {}.'.format(self.name))

        quotes = {}

        locale.setlocale(locale.LC_NUMERIC, "de_DE.UTF-8")

        d = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

        while start_date <= d:
            # Get quotes from Ariva
            self.logger.debug("Fetching quotes for {} of {}".format(d.strftime('%B'), d.strftime('%Y')))
            url = self.url.split('?')[0] + '/historische_kurse?' + self.url.split('?')[1] + '&month={}'.format(d.strftime('%Y-%m-%d'))
            req = urllib.request.urlopen(url)
            html = req.read().decode('utf-8')
            soup = BS(html,'lxml')

            self.logger.debug("URL is '{}'".format(url))

            for tr in soup.find('div', id='pageHistoricQuotes').findAll('tr', class_='arrow0'):
                cells = tr.findAll('td')
                quote_date = datetime.strptime(cells[0].contents[0], '%d.%m.%y').date()
                if quote_date <= end_date and quote_date >= start_date:
                    # close = float('.'.join(cells[4].contents[0].split(',')))
                    close = locale.atof(cells[4].contents[0])
                    quotes[quote_date] = close

            # we need to get the *last* day of the previous month
            d = d + relativedelta(months=-1)
            d = date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])

        return quotes
