import logging
import urllib.request
from bs4 import BeautifulSoup as BS

class PriceSource:

    def make_url(self): # TODO: provide interface for historical quote URL also
        return None

    def __init__(self, symbol):
        # if not hasattr(self, 'name'): self.name = None
        self.symbol = symbol
        self.sec_type = None
        self._url = None

        self.logger = logging.getLogger('{}.{}'.format(self.name, self.symbol))

    @property
    def url(self):
        # we lazily set the url, since make_url() could contain expensive operations
        if not self._url:
            self._url = self.make_url()
            self.logger.debug('URL is {}'.format(self._url))
        return self._url

    def fetch_site(self):
        html = urllib.request.urlopen(self.url).read().decode('utf-8')
        return BS(html,"lxml")

    def fetch_info(self):
        raise NotImplementedError()

    def fetch_historic_quotes(self):
        raise NotImplementedError()

    def security(self, class_=None):
        info = self.fetch_info()

        if class_ is None and self.sec_type is not None:
            self.logger.debug('Security is of type {}'.format(self.sec_type))
            class_ = self.sec_type
        if class_ is None:
            self.logger.warning('Could not determine security type.')
            class_ = Security
        sec = class_(self.symbol)

        sec.update_from_dict(info)
        sec.update_hook = self.fetch_info
        sec.update_hook_historic = self.fetch_historic_quotes
        return sec
