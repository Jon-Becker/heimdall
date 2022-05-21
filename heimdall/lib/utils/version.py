import pip_api
import requests
import json

from ..config import *

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

def update():
  pass