import json
import pathlib

from .utils.io import write, loadFileAsJson

def getConfig():
  try:
    return loadFileAsJson(f'{pathlib.Path(__file__).parent.parent.resolve()}/env/conf.json')
  except:
    # config file is missing, create it
    conf = {
      "build": {
        "version": "v1.0.3-stable"
      },
      "autoupdate": False,
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
    
    with open(getConfigPath(), 'w') as outfile:
      json.dump(conf, outfile, indent=4)
    return conf

# get the config file path, because it can be hidden in pypi directories
def getConfigPath():
  return f'{pathlib.Path(__file__).parent.parent.resolve()}/env/conf.json'