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
        "version": "1.0.1-rc.6"
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