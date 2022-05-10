import requests
import json

import lib.config

def getLocalVersion():
  return lib.config.getConfig()['build']['version']

def getLatestRelease():
  try:
    releaseRequest = requests.get('https://api.github.com/repos/Jon-Becker/heimdall/releases', timeout=3)
    if releaseRequest.status_code == 200:
      request_body = json.loads(releaseRequest.text)
      return request_body
    return False
  except:
    return False

def getLatestSolidityRelease():
  try:
    releaseRequest = requests.get('https://api.github.com/repos/ethereum/solidity/releases', timeout=3)
    if releaseRequest.status_code == 200:
      request_body = json.loads(releaseRequest.text)
      return request_body[0]['tag_name'].replace("v", "^")
    return '>=0.8.0'
  except:
    return '>=0.8.0'

def getRemoteVersion():
  try:
    latestRelease = getLatestRelease()
    if latestRelease != False:
      return latestRelease[0]["name"]
    return False
  except:
    return False

def update():
  pass