import json
import re
import pip_api
import requests

from ..config import *
from .logger import log
from .colors import colorLib

# Gets the latest version of eth-heimdall from PyPi
def getRemoteVersion():
  releaseRequest = requests.get('https://pypi.python.org/pypi/eth-heimdall/json', timeout=3)
  if releaseRequest.status_code == 200:
    latestVersionBody = json.loads(releaseRequest.text)
    return str(latestVersionBody['info']['version'].strip())
  return getLocalVersion()

# gets the local version of eth-heimdall
def getLocalVersion():
  try:
    return str(pip_api.installed_distributions(local=False)['eth-heimdall'].version)
  except:
    return str(getConfig()['build']['version'])
  
# gets the latest stable release of solidity from github
def getLatestSolidityRelease():
  try:
    releaseRequest = requests.get('https://api.github.com/repos/ethereum/solidity/releases', timeout=3)
    if releaseRequest.status_code == 200:
      request_body = json.loads(releaseRequest.text)
      return request_body[0]['tag_name'].replace("v", "^")
    return '>=0.8.0'
  except:
    return '>=0.8.0'
  
# performs a check to see if local version == remote version
def checkVersionUpToDate():
  remoteVersion = getRemoteVersion()
  localVersion = getLocalVersion()
  remoteVersionList = re.sub(r'[^0-9\.]' , '' , remoteVersion).split('.')
  localVersionList = re.sub(r'[^0-9\.]' , '' , localVersion).split('.')
  
  # Check each remote version according to SemVer and compare to local version
  isUpToDate = not ((remoteVersionList[0] > localVersionList[0]) or (remoteVersionList[1] > localVersionList[1]) or (remoteVersionList[2] > localVersionList[2]))
  
  return (isUpToDate, remoteVersion)

# performs a silent update of eth-heimdall through pip
def update(version):
  config = getConfig()
  if 'autoupdate' in config and config['autoupdate'] == True:
    log('info', f'Installing latest version {colorLib.CYAN + version[1] + colorLib.RESET}...')
    from subprocess import DEVNULL, STDOUT, check_call
    
    check_call(['python3', '-m', 'pip', 'install', 'eth-heimdall', '-U'], stdout=DEVNULL, stderr=STDOUT)

    if checkVersionUpToDate()[0]:
      log('success', f'Successfully updated to eth-heimdall {colorLib.GREEN + getLocalVersion() + colorLib.RESET}.')
    else:
      log('critical', 'Failed to install newest version of eth-heimdall from PyPi!')
  else:
    log('alert', f'You can update to version {colorLib.GREEN}{version[1]}{colorLib.RESET} by running: {colorLib.GREEN}pip install eth-heimdall=={version[1]} --U{colorLib.RESET} !')
    log('info', f'You can toggle autoupdates by running {colorLib.CYAN}heimdall config --autoupdate{colorLib.RESET}.')