from .security import Security

class ETF(Security):

    def __init__(self, symbol, read_quotes=True):
        Security.__init__(self, symbol, read_quotes)

    def __repr__(self):
        return '<ETF: symbol {}>'.format(self.symbol)
