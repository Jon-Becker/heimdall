from setuptools import Extension
from setuptools import setup

setup(name='eth_heimdall',
      version='1.0.3b7',
      description='Heimdall is an advanced and modular smart-contract toolkit which aims to make dealing with smart contracts on EVM based chains easier.',
      url='https://github.com/Jon-Becker/heimdall',
      entry_points={'console_scripts': ['heimdall=heimdall.__main__:main']},
      keywords=['ethereum', 'evm', 'decompiler', 'evm decompiler', 'smart contract', 'smart contract decompiler', 'evm smart contract decompiler', 'eth contract decompiler'],
      author='Jonathan Becker (jon-becker)',
      author_email='jonathan@jbecker.dev',
      license='MIT',
      
      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Software Development :: Disassemblers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Utilities'
      ],
      
      packages=[
        'heimdall',
        'heimdall/lib',
        'heimdall/logs',
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
          'eth_abi',
          'eth_abi',
          'pip-api',
          'platform',
          'numexpr',
      ],
)