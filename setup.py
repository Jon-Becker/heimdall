from setuptools import Extension
from setuptools import setup

setup(name='heimdall',
      version='1.0.0-rc.1',
      description='Heimdall is an advanced and modular smart-contract toolkit which aims to make dealing with smart contracts on EVM based chains easier.',
      url='https://github.com/Jon-Becker/heimdall',
      entry_points={'console_scripts': ['heimdall=heimdall.__main__:main']},
      keywords=['ethereum', 'evm', 'decompiler', 'evm decompiler', 'smart contract', 'smart contract decompiler', 'evm smart contract decompiler', 'eth contract decompiler'],
      author='Jonathan Becker (jon-becker)',
      author_email='jonathan@jbecker.dev',
      license='MIT',
      packages=['heimdall'],
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
