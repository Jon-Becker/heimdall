import json
import os
import hashlib
import pickle
from .logger import log
from .colors import colorLib

# gets the output directory of a given run
def outputDirectory(outpath, target):
  if outpath:
    output = f'{outpath}/{target}/'
  else:
    output = f'{os.getcwd()}/output/{target}'
  
  # if the path doesnt exist, make it
  if not os.path.exists(output):
    log('info', f'Creating output directory {colorLib.CYAN}{output.replace(os.getcwd(), ".")}{colorLib.RESET}')
    os.makedirs(output)
  
  return output

# write to a file
def write(file, lines):
  with open(file,'w') as f:
    f.write(lines)

# delete a file if it exists
def delete(file):
  if os.path.exists(file):
    os.remove(file)

# write an object to a file as a pickle object
def writeObj(file, lines):
  with open(file,'wb') as f:
    pickle.dump(lines, f)

# make a path if it doesnt exist
def makePath(dirPath):
  if not os.path.exists(dirPath):
    log('info', f'Creating source directory {colorLib.CYAN}{dirPath.replace(os.getcwd(), ".")}{colorLib.RESET}')
    os.makedirs(dirPath)
  return dirPath

# append a single line to a file
def appendLine(file, line):
  if not os.path.exists(file):
    with open(file,'w') as f:
      f.write(line)
  else:
    with open(file,'a') as f:
      f.write(line)

# returns whether or not a file exists
def pathExists(dirPath):
  return os.path.exists(dirPath)

# reads lines from a file path
def readFile(path):
  with open(path) as f:
    lines = f.readlines()
  return lines

# calculates a directories checksum by calculating the ,d5 hash of all files in the directory
def checksum(directory, result=None):
  result = result if result else ''
  for item in os.listdir(directory):
    if item.endswith("py"):
      result = hashlib.md5((str(open(f'{directory}/{item}','rb').read()) + result).encode('utf-8')).hexdigest()
    elif "." not in item:
      result = checksum(f'{directory}/{item}', result)
      
  return result

# writes a json object to the config file after changing pair {name: value}
def write_config_value_at_path(path, name, value):
    with open(path, 'r') as f:
        config = json.load(f)
        config[name] = value
    with open(path, 'w') as f:
        json.dump(config, f, indent=4)
        
        
# load a file as  a json object
def loadFileAsJson(path):
  with open(path) as pathFile:
    contents = json.loads("".join(pathFile.readlines()))
  return contents

# load a file as a pickle object
def loadFileAsPickle(path):
  with open(path, 'rb') as pathFile:
    contents = pickle.load(pathFile)
  return contents