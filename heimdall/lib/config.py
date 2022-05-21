import json
import pickle
import pathlib

from .utils.io import write

def getConfig():
  try:
    return loadFileAsJson(f'{pathlib.Path(__file__).parent.parent.resolve()}/env/conf.json')
  except:
    conf = {
      "build": {
        "version": "v1.0.2-stable"
      },
      "defaults": {

        "providers": {
          "local": "http://127.0.0.1:7545",
          "remote": "https://mainnet.infura.io/v3/"
        }

      },

      "environment": {
        "apis": {
          "etherscan": ""
        }
      }
    }
    json.dump(conf, f'{pathlib.Path(__file__).parent.parent.resolve()}/env/conf.json')
    return conf

def loadFileAsJson(path):
  with open(path) as pathFile:
    contents = json.loads("".join(pathFile.readlines()))
  return contents

def loadFileAsPickle(path):
  with open(path, 'rb') as pathFile:
    contents = pickle.load(pathFile)
  return contents

def getConfigPath():
  return f'{pathlib.Path(__file__).parent.parent.resolve()}/env/conf.json'