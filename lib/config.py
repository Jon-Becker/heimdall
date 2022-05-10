import json
import pickle

def getConfig():    
  return loadFileAsJson('env/conf.json')

def loadFileAsJson(path):
  with open(path) as pathFile:
    contents = json.loads("".join(pathFile.readlines()))
  return contents

def loadFileAsPickle(path):
  with open(path, 'rb') as pathFile:
    contents = pickle.load(pathFile)
  return contents