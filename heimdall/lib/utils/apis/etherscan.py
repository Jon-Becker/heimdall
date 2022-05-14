from cmath import e
import os
import json
import time
import requests

from ..logger import log
from ..colors import colorLib
from ..io import outputDirectory, write, makePath

def fetchSourceCode(args, output, onlyAbi=False):
  log('info', 'Attempting to fetch source from EtherScan...')
  try:
    sourceRequest = requests.get(f'https://api.etherscan.io/api?module=contract&action=getsourcecode&address={args.target}')
    if sourceRequest.status_code == 200:
      sourceBody = json.loads(sourceRequest.text)
      
      source = sourceBody['result'][0]['SourceCode'].replace("}}", "}", 1).replace("{{", "{", 1)
      abi = sourceBody['result'][0]['ABI']
      if args.verbose:
        log('info', f'Saving ABI file {colorLib.CYAN}{output.replace(os.getcwd(), ".")}/abi.json{colorLib.RESET}')
        
      try:
        abi = json.loads(abi)
        write(f'{output}/abi.json', json.dumps(abi, indent=2))
      except:
        log('critical', 'Writing ABI excepted! Defaulting to assembly builder.')
        return False
      
      if len(source) > 0:
        log('success', 'Found verified source on EtherScan!')

        sourceType = "Solidity"
        sourceExtension = "sol"
        if "vyper" in sourceBody['result'][0]['CompilerVersion'].lower():
          sourceType = "Vyper"
          sourceExtension = "vy"
        if args.verbose:
          log('info', f'Compiler language is {colorLib.CYAN}{sourceType}{colorLib.RESET}.')

        if not onlyAbi:
          try:
            sourceObject = json.loads(source)
            try:
              if args.verbose:
                log('info', 'Multiple file source detected!')
              sourcePath = makePath(f'{output}/source/')
              for key in sourceObject['sources']:
                if args.verbose:
                  log('info', f'Saving source file {colorLib.CYAN}{sourcePath.replace(os.getcwd(), ".")}{key}{colorLib.RESET}')
                dirPath = key.split("/")
                sourceName = dirPath.pop()
                dirpath = f'{sourcePath}{"/".join(dirPath)}'
                if not os.path.exists(dirpath):
                  os.makedirs(dirpath)
                write(f'{dirpath}/{sourceName}', sourceObject['sources'][key]['content'])
            except:
              log('critical', 'Fetching source excepted! Defaulting to assembly builder.')
              return False
            
          except:
            if args.verbose:
              log('info', 'Single file source detected!')
            write(f'{output}/source.{sourceExtension}', source)
            log('info', f'Saving source file {colorLib.CYAN}{output.replace(os.getcwd(), ".")}/source.{sourceExtension}{colorLib.RESET}')
            
        log('success', f'Successfully retrieved contract source from EtherScan. Output saved to {colorLib.GREEN}{output.replace(os.getcwd(), ".")}{colorLib.RESET}.')
        return abi
        
      else:
        log('warning', 'No verified source found on EtherScan. Defaulting to assembly builder.')
        return False
    log('critical', 'Fetching source from EtherScan failed! Defaulting to assembly builder.')
    return False
  except:
    log('critical', 'Fetching source excepted! Defaulting to assembly builder.')
    return False
  
def fetchDeploymentBytecode(args, output):
  log('info', 'Attempting to fetch deployment bytecode from EtherScan...')
  try:
    sourceRequest = requests.get(f'https://api.etherscan.io/api?module=account&action=txlist&address={args.target}&startblock=0&endblock=99999999999&page=1&offset=1&sort=asc')
    if sourceRequest.status_code == 200:
      sourceBody = json.loads(sourceRequest.text)
      if "NOT" in sourceBody['message']:
        if "rate limit" in sourceBody['result']:
          if args.verbose:
            log('warning', 'Etherscan rate-limited! Sleeping for 5 seconds.')
          time.sleep(5.01)
          return fetchDeploymentBytecode(args, output)
        else:
          log('critical', 'Couldn\'t fetch deployment bytecode from EtherScan.')
          return False
      else:
        if len(sourceBody['result']) > 0:
          return sourceBody['result'][0]['input']
                    
    log('critical', 'Fetching deployment bytecode from EtherScan failed!')
    return False
  except Exception as e:
    log('critical', 'Fetching deployment bytecode from EtherScan excepted!')
    return False