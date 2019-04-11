from setuptools import setup

setup(name='ppserve',
      description='Serves prices of financial securities fetched from the internet in a format that Portfolio Performance understands',
      version='0.1',
      url='https://github.com/fberg/ppserve',
      author='Franz Berger',
      license='GPL-3',
      packages=[
          'ppserve',
          'ppserve.price_sources',
          'ppserve.securities'
      ],
      scripts=['bin/ppserve'],
      install_requires=[
          'PyYAML',
          'bs4',
          'lxml',
          'coloredlogs',
          'termcolor',
          'bottle',
          'paste',
          'CurrencyConverter',
          'python-dateutil'
      ],
      include_package_data=True
)
