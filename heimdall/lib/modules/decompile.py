from hashlib import sha256

from web3 import Web3

from ..config import *
from ..utils.logger import log, query
from ..utils.colors import colorLib
from ..utils.io import outputDirectory, pathExists, readFile, write
from ..utils.eth.disassembler import disassemble
from ..utils.eth.builder import build
from ..utils.apis.etherscan import fetchSourceCode
from ..utils.eth.version import detectVersion, resolve

meta = {
  "title": "Decompile",
  "description": "Decompile and download the target smart contract",
  "author": "Jonathan Becker <jonathan@jbecker.dev>",
  "version": "v1.0.0",
}

def main(args):
  if args.target:
    target = args.target
    output = args.output

    args.local = pathExists(args.target)
    
    if not args.local:
      if not args.provider:
        args.provider = getConfig()['defaults']['providers']['remote']
        log('warning', f'Provider not set! Using default remote provider from configuration.')
        
        log('info', 'Establishing connection to provider...')
      else:
        if "http" in args.provider.lower():
          web3 = Web3(Web3.HTTPProvider(args.provider, request_kwargs={'timeout': 3}))
        elif "wss" in args.provider.lower():
          web3 = Web3(Web3.WebsocketProvider(args.provider, request_kwargs={'timeout': 3}))
        else:
          log('critical', f'Provider {colorLib.RED}{args.provider}{colorLib.RESET} doesn\'t seem valid.')
          return

        if web3.isConnected():
          log('success', 'Connection established!')
        else:
          log('warn', f'Connection to {colorLib.YELLOW}{args.provider}{colorLib.RESET} failed!')
          web3 = Web3()
          return
      
      log('info', f'Fetching target {colorLib.CYAN}{target}{colorLib.RESET}...')
      if not 'eth' in target:
        target = Web3.toChecksumAddress(target.lower())
      rawBytecode = web3.eth.get_code(target)
      bytecode = "".join(["{:02x}".format(v) for v in rawBytecode])

      if len(bytecode) <= 1:
        log('warn', f'Target {colorLib.CYAN}{target}{colorLib.RESET} doesn\'t appear to be a contract address.')
        return
    else:
      web3 = Web3()
      bytecode = readFile(args.target)[0]
      target = f'Local_0x{sha256(bytecode.encode("UTF-8")).hexdigest()[15:]}'
      args.target = "0x" + target
      
      if not bytecode.startswith("0x") or " " in bytecode:
        log('critical', f'The file provided doesn\'t contain valid bytecode!')
        return
      
      bytecode = bytecode[2:]
      
    output = outputDirectory(output, target)
    
    write(f'{output}/bytecode.evm' , f'0x{bytecode}')
    
    if not args.default:
      fetchFromEtherscan = query('info', "N", f'Would you like to attempt to fetch source from EtherScan? Otherwise, we will build source from assembly. [y/N]: ')
    else:
      fetchFromEtherscan = "N"
      log('info', f'Would you like to attempt to fetch source from EtherScan? Otherwise, we will build source from assembly. [y/N]: N')

    sourceFetched = False
    if fetchFromEtherscan == "Y":
      sourceFetched = fetchSourceCode(args, output)
      
    if sourceFetched == False:
      assembly = disassemble(bytecode, output, args)
      version = detectVersion(assembly, args)
      
      if args.verbose:
          log('info', f'Assembly heuristics suggest {colorLib.CYAN}{resolve(version[0][0])} <= EVM < {resolve(version[1][0])}{colorLib.RESET} and {colorLib.CYAN}Solidity >= {version[0][1]}{colorLib.RESET}.')
      
      if version[0][0] < 2:
        log('warning', f'Heimdall currently only has support for EVM versions after Constantinople. This contract may not decompile correctly.')
        
      log('info', 'Attempting to build source files from assembly...')

      source = build(assembly, args, output, web3)

  else:
    print('heimdall: error: Missing a mandatory option -t. Use -h to show the help menu.\n')
    return