import os
import pathlib
import datetime
import re
from alive_progress import alive_it

from .colors import colorLib

global logfile
logfile = f'{pathlib.Path(__file__).parent.parent.parent.resolve()}/logs/heimdall-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.log'

def initLogfile(command):
  logStripColor(logfile , "info", " ".join(command))

def logStripColor(file, type, log):
  with open(file,'a') as f:
    f.write(re.sub(r'(\\033|)\[\d*m', '', "{} {}\n".format(get_prefix(type), log)))

def logTraceback(error, silent=False):
  traceback = error.strip().split("\n")
  errorLogString = f'Execution excepted: {traceback[-1]}'
  tracebackFiles = []
  for file in (traceback):
    if "File \"/" in file:
      tracebackFiles.append("".join(", ".join(file.split(", ")[0:2]).split('"')[1:]))
  
  for i, file in enumerate(tracebackFiles):
    errorLogString += f'\n{" "*29}{"├" if i+1 < len(tracebackFiles) else "└"}─({colorLib.RED}{i}{colorLib.RESET}) {file}'
  
  log("critical", errorLogString, silent)

def log(type, message, silent=False):
  if(type == "warning"):
    accent = colorLib.YELLOW
  elif(type == "critical"):
    accent = colorLib.RED
  elif(type == "success"):
    accent = colorLib.GREEN
  elif(type == "alert"):
    accent = colorLib.GREEN + colorLib.BOLD
  else:
    accent = colorLib.CYAN
  if not silent:
    print(datetime.datetime.now().strftime(f'[{accent}%H:%M:%S.%f{colorLib.RESET}] [{accent}{type.upper()}{colorLib.RESET}] {message}'))
    
  logStripColor(logfile, type, message)

def query(type, default, message):
  if(type == "warning"):
    accent = colorLib.YELLOW
  elif(type == "critical"):
    accent = colorLib.RED
  elif(type == "success"):
    accent = colorLib.GREEN
  else:
    accent = colorLib.CYAN

  response = input(datetime.datetime.now().strftime(f'[{colorLib.CYAN}%H:%M:%S.%f{colorLib.RESET}] [{accent}{type.upper()}{colorLib.RESET}] {message}'))
  if len(response) < 1:
    return default
  return response

def get_prefix(type):
  if(type == "warning"):
    accent = colorLib.YELLOW
  elif(type == "critical"):
    accent = colorLib.RED
  elif(type == "success"):
    accent = colorLib.GREEN
  else:
    accent = colorLib.CYAN

  return(datetime.datetime.now().strftime(f'[{accent}%H:%M:%S.%f{colorLib.RESET}] [{accent}{type.upper()}{colorLib.RESET}]'))

def progress_bar(items, args):
  if args.verbose:
    return alive_it(items,title=get_prefix("info"), enrich_print=False, receipt=False, spinner=False, stats='(eta: {eta})')
  return items
