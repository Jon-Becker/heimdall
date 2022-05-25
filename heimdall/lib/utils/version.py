import json
import pip_api
import requests

from ..config import *
from .logger import log
from .colors import colorLib

def getRemoteVersion():
  releaseRequest = requests.get('https://pypi.python.org/pypi/eth-heimdall/json', timeout=3)
  if releaseRequest.status_code == 200:
    latestVersionBody = json.loads(releaseRequest.text)
    return str(latestVersionBody['info']['version'].strip())
  return getLocalVersion()

def getLocalVersion():
  try:
    return str(pip_api.installed_distributions(local=False)['eth-heimdall'].version)
  except:
    return str(getConfig()['build']['version'])
  
def getLatestSolidityRelease():
  try:
    releaseRequest = requests.get('https://api.github.com/repos/ethereum/solidity/releases', timeout=3)
    if releaseRequest.status_code == 200:
      request_body = json.loads(releaseRequest.text)
      return request_body[0]['tag_name'].replace("v", "^")
    return '>=0.8.0'
  except:
    return '>=0.8.0'
  
def checkVersionUpToDate():
  remoteVersion = getRemoteVersion()
  localVersion = getLocalVersion()
  return (remoteVersion == localVersion, remoteVersion)

def update(version):
  config = getConfig()
  if 'autoupdate' in config and config['autoupdate'] == True:
    log('info', f'Installing latest version {colorLib.CYAN + version[1] + colorLib.RESET}...')
    from subprocess import DEVNULL, STDOUT, check_call
    
    result = check_call(['python3', '-m', 'pip', 'install', 'eth-heimdall', '-U'], stdout=DEVNULL, stderr=STDOUT)

    if checkVersionUpToDate()[0]:
      log('success', f'Successfully updated to eth-heimdall {colorLib.GREEN + getLocalVersion() + colorLib.RESET}.')
    else:
      log('critical', 'Failed to install newest version of eth-heimdall from PIP!')
  else:
    log('alert', f'You can update to version {colorLib.GREEN}{version[1]}{colorLib.RESET} by running: {colorLib.GREEN}pip install eth-heimdall --upgrade{colorLib.RESET} !')
    log('info', f'You can toggle autoupdates by running {colorLib.CYAN}heimdall -m config --toggle-autoupdate{colorLib.RESET}.')