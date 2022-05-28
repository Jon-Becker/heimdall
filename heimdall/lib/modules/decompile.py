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

    # if the path exists, it's a local decompilation and the path contains bytecode
    args.local = pathExists(args.target)
    
    # its not a local file
    if not args.local:
      if not args.provider:
        args.provider = getConfig()['defaults']['providers']['remote']
        log('warning', f'Provider not set! Using default remote provider from configuration.')
       
      # try to connect to the web3 provider
      log('info', 'Establishing connection to provider...')
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
        return
      
      # fetch bytecode from web3
      log('info', f'Fetching target {colorLib.CYAN}{target}{colorLib.RESET}...')
      if not 'eth' in target:
        target = Web3.toChecksumAddress(target.lower())
      rawBytecode = web3.eth.get_code(target)
      bytecode = "".join(["{:02x}".format(v) for v in rawBytecode])
      
      # verify that the target is valid
      if len(bytecode) <= 1:
        log('warn', f'Target {colorLib.CYAN}{target}{colorLib.RESET} doesn\'t appear to be a contract address.')
        return
    else:
      # its a local file, we don't need to connect to web3. Fetch bytecode from the local file
      web3 = Web3()
      bytecode = readFile(args.target)[0]
      target = f'Local_0x{sha256(bytecode.encode("UTF-8")).hexdigest()[15:]}'
      args.target = "0x" + target
      
      # verify the bytecode is valid
      if not bytecode.startswith("0x") or " " in bytecode:
        log('critical', f'The file provided doesn\'t contain valid bytecode!')
        return
      bytecode = bytecode[2:]
      
    # create the output directory and save the target bytecode to it
    output = outputDirectory(output, target)
    write(f'{output}/bytecode.evm' , f'0x{bytecode}')
    
    # should we ignore decompilation completely and fetch source from etherscan?
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
      
      # log a warning if the version if unsupported
      log('info', f'Assembly heuristics suggest {colorLib.CYAN}{resolve(version[0][0])} <= EVM < {resolve(version[1][0])}{colorLib.RESET} and {colorLib.CYAN}Solidity >= {version[0][1]}{colorLib.RESET}.', True)
      if version[0][0] < 2:
        log('warning', f'Heimdall currently only has support for EVM versions after Constantinople. This contract may not decompile correctly.')
        
      # run the main decompilation build process
      log('info', 'Attempting to build source files from assembly...')
      source = build(assembly, args, output, web3)

  else:
    print('heimdall: error: Missing a mandatory option -t. Use -h to show the help menu.\n')
    return