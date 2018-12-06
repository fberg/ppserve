from .security import Security

class Stock(Security):

    def __init__(self, symbol, read_quotes=True):
        Security.__init__(self, symbol, read_quotes)

    def __repr__(self):
        return '<Stock: symbol {}>'.format(self.symbol)
