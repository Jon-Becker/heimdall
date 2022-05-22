import os
import hashlib
import pickle
from .logger import log
from .colors import colorLib

def outputDirectory(outpath, target):
  if outpath:
    output = f'{outpath}/{target}/'
  else:
    output = f'{os.getcwd()}/output/{target}'

  if not os.path.exists(output):
    log('info', f'Creating output directory {colorLib.CYAN}{output.replace(os.getcwd(), ".")}{colorLib.RESET}')
    os.makedirs(output)
  return output

def write(file, lines):
  with open(file,'w') as f:
    f.write(lines)

def delete(file):
  if os.path.exists(file):
    os.remove(file)

def writeObj(file, lines):
  with open(file,'wb') as f:
    pickle.dump(lines, f)

def makePath(dirPath):
  if not os.path.exists(dirPath):
    log('info', f'Creating source directory {colorLib.CYAN}{dirPath.replace(os.getcwd(), ".")}{colorLib.RESET}')
    os.makedirs(dirPath)
  return dirPath

def appendLine(file, line):
  if not os.path.exists(file):
    with open(file,'w') as f:
      f.write(line)
  else:
    with open(file,'a') as f:
      f.write(line)

def pathExists(dirPath):
  return os.path.exists(dirPath)

def readFile(path):
  with open(path) as f:
    lines = f.readlines()
  return lines

def checksum(directory, result=None):
  result = result if result else ''
  for item in os.listdir(directory):
    if item.endswith("py"):
      result = hashlib.md5((str(open(f'{directory}/{item}','rb').read()) + result).encode('utf-8')).hexdigest()
    elif "." not in item:
      result = checksum(f'{directory}/{item}', result)
      
  return result