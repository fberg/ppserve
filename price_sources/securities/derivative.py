from .security import Security

class Derivative(Security):

    def __init__(self, symbol, read_quotes=True):
        Security.__init__(self, symbol, read_quotes)

    def __repr__(self):
        return '<Derivative: symbol {}>'.format(self.symbol)
