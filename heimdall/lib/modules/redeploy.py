import os
import datetime

import lib.config
from lib.utils.eth.builder import build
from web3 import Web3

from lib.utils.logger import log, query
from lib.utils.colors import colorLib
from lib.utils.io import outputDirectory, write
from lib.utils.eth.disassembler import disassemble
from lib.utils.apis.etherscan import fetchSourceCode, fetchDeploymentBytecode
from lib.utils.eth.version import detectVersion, resolve

meta = {
  "title": "Redeploy",
  "description": "Download and redeploy the target smart contract",
  "author": "Jonathan Becker <jonathan@jbecker.dev>",
  "version": "v1.0.0",
}


def main(args):
  if args.target:
    target = args.target
    output = args.output

    localRPC = lib.config.getConfig()['defaults']['providers']['local']

    if not args.provider:
      args.provider = lib.config.getConfig()['defaults']['providers']['remote']
      log('warning', f'Provider not set! Using default remote provider from configuration.')
      
    log('info', 'Establishing connection to remote provider...')
    if "http" in args.provider.lower():
      web3fetch = Web3(Web3.HTTPProvider(args.provider))
    elif "wss" in args.provider.lower():
      web3fetch = Web3(Web3.WebsocketProvider(args.provider))
    else:
      log('critical', f'Provider {colorLib.RED}{args.provider}{colorLib.RESET} doesn\'t seem valid.')
      return

    if web3fetch.isConnected():
      log('success', 'Connection established!')
    else:
      log('critical', f'Connection to {colorLib.RED}{args.provider}{colorLib.RESET} failed!')
      return
    
    log('info', 'Establishing connection to local network...')
    if "http" in localRPC.lower():
      web3 = Web3(Web3.HTTPProvider(localRPC))
    elif "wss" in localRPC.lower():
      web3 = Web3(Web3.WebsocketProvider(localRPC))
    else:
      log('critical', f'Provider {colorLib.RED}{localRPC}{colorLib.RESET} doesn\'t seem valid.')
      return

    if web3.isConnected():
      log('success', 'Connection established!')
    else:
      log('critical', f'Connection to {colorLib.RED}{localRPC}{colorLib.RESET} failed!')
      return



    log('info', f'Fetching target {colorLib.CYAN}{target}{colorLib.RESET}...')
    if not 'eth' in target:
      target = Web3.toChecksumAddress(target.lower())
    rawBytecode = web3fetch.eth.get_code(target)
    bytecode = "".join(["{:02x}".format(v) for v in rawBytecode])

    if len(bytecode) <= 1:
      log('warn', f'Target {colorLib.CYAN}{target}{colorLib.RESET} doesn\'t appear to be a contract address.')
      return

    output = outputDirectory(output, target)
    
    write(f'{output}/bytecode.evm' , f'0x{bytecode}')
    fetchFromEtherscan = "Y"
    
    if not args.default:
      fetchFromEtherscan = query('info', "N", f'Would you like to attempt to fetch contract ABI from EtherScan? Otherwise, we will build it from assembly. [Y/n]: ')
    else:
      log('info', f'Would you like to attempt to fetch contract ABI from EtherScan? Otherwise, we will build it from assembly. [Y/n]: Y')
      
    abi = None
    if fetchFromEtherscan == "Y":
      abi = fetchSourceCode(args, output, True)
      
    if not abi:
      assembly = disassemble(bytecode, output, args)
      version = detectVersion(assembly, args)
      
      if args.verbose:
          log('info', f'Assembly heuristics suggest {colorLib.CYAN}{resolve(version[0][0])} <= EVM < {resolve(version[1][0])}{colorLib.RESET} and {colorLib.CYAN}Solidity >= {version[0][1]}{colorLib.RESET}.')
      
      if version[0][0] < 2:
        log('warning', f'Heimdall currently only has support for EVM versions after Constantinople.')
        return
        
      log('info', 'Attempting to build source files from assembly...')

      abi = build(assembly, args, output, web3fetch, onlyAbi=True)['abi']
    
    if abi:
      bytecode = fetchDeploymentBytecode(args, output)
      try:
        contract = web3.eth.contract(abi=abi, bytecode=bytecode,)
        tx = {
          'from': web3.eth.accounts[0]
        }
        constructor_args = []
        for i, constructor_arguments in enumerate(abi[0]['inputs']):
          if i == 0:
            log('info', 'This contract has required constructor arguements: ')
          constructor_arg = input(f'{" "*25}{"├" if i+1 < len(abi[0]["inputs"]) else "└"}─({colorLib.CYAN}{constructor_arguments["type"]}{colorLib.RESET}) {constructor_arguments["name"]}: ')
          constructor_args.append( bytes.fromhex(constructor_arg[2:]) if "0x" in constructor_arg else bytes.fromhex(hex(int(constructor_arg))[2:]) )
                  
        print(*constructor_args)
        tx_hash = contract.constructor(*constructor_args).transact(tx)
        if args.verbose:
          log('info', f'Contract deployment submitted with TXID: {colorLib.CYAN}{tx_hash.hex()}{colorLib.RESET}.')
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt.contractAddress:
          log('info', f'Transaction confirmed! Contract redeployed on development environment as {colorLib.CYAN}{tx_receipt.contractAddress}{colorLib.RESET}.')
          
          if args.verbose:
            log('info', f'Transaction included in block {colorLib.CYAN}{tx_receipt.blockNumber}{colorLib.RESET}. Total gas consumption was {colorLib.CYAN}{tx_receipt.cumulativeGasUsed}{colorLib.RESET}.')
          return
        return
        
      except Exception as e:
        log('critical', f'Redeploying bytecode failed! Logs saved to {colorLib.CYAN}{output.replace(os.getcwd(), ".")}/{datetime.date.today().strftime("%m-%d-%Y")}.log{colorLib.RESET}')
        return
    else:
      log('critical', f'Could not read contract ABI.')
  else:
    print('heimdall: error: Missing a mandatory option -t. Use -h to show the help menu.\n')
    return