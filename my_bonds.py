from datetime import date
from price_sources.securities import Bond
from price_sources import ArivaPriceSource

import logging
logger = logging.getLogger('my_bonds')

import yaml
from pathlib import Path

script_path = Path(__file__).parent/'my_bonds.yaml'

try:
    data = yaml.load(open(script_path, 'r').read())
except FileNotFoundError:
    data = {}

# Sanitize symbols; they may be of integer type if entered without quotes
for symbol, info in data.items():
    if type(symbol) != str:
        data[str(symbol)] = info
        del data[symbol]

my_bonds = {}

# load bonds from my_bonds
for symbol, info in data.items():
    logger.info('Loading {}'.format(symbol))
    bond = Bond(symbol)
    bond.update_from_dict(info)
    ps = ArivaPriceSource(symbol)
    bond.update_from_dict({
        'update_hook': ps.fetch_info,
        'update_hook_historic': ps.fetch_historic_quotes
    })

    my_bonds[symbol] = bond
