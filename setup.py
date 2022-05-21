from setuptools import Extension
from setuptools import setup

setup(name='eth_heimdall',
      version='1.0.2-rc1',
      description='Heimdall is an advanced and modular smart-contract toolkit which aims to make dealing with smart contracts on EVM based chains easier.',
      url='https://github.com/Jon-Becker/heimdall',
      entry_points={'console_scripts': ['heimdall=heimdall.__main__:main']},
      keywords=['ethereum', 'evm', 'decompiler', 'evm decompiler', 'smart contract', 'smart contract decompiler', 'evm smart contract decompiler', 'eth contract decompiler'],
      author='Jonathan Becker (jon-becker)',
      author_email='jonathan@jbecker.dev',
      license='MIT',
      packages=[
        'heimdall',
        'heimdall/lib',
        'heimdall/lib/menus',
        'heimdall/lib/modules',
        'heimdall/env',
        'heimdall/lib/utils',
        'heimdall/lib/utils/apis',
        'heimdall/lib/utils/eth',
        'heimdall/lib/utils/eth/classes'
        ],
      install_requires=[
          'requests',
          'web3',
          'numpy',
          'bidict',
          'alive-progress',
          'argparse',
          'argcomplete',
          'eth_abi'
      ],
      )

# Md36&deveZgNiJqN6HAXn