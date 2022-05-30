import os
import pathlib
import datetime
import re
from alive_progress import alive_it

from .colors import colorLib

global logfile
logfile = f'{pathlib.Path(__file__).parent.parent.parent.resolve()}/logs/heimdall-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.log'

# purge old log files
def purgeOldLogfiles():
  try:
    files = os.listdir(f'{pathlib.Path(__file__).parent.parent.parent.resolve()}/logs')
    files.remove('__init__.py')
    for file in files:
        if int(file.split('-')[1].replace('.log', '')) < int(datetime.datetime.now().strftime("%Y%m%d%H%M%S")) - 100000:
          os.remove(f'{pathlib.Path(__file__).parent.parent.parent.resolve()}/logs/{file}')
      # if timestamp is over 1 day old
  except: pass
      
# log to file, removing color codes
def logStripColor(file, type, log):
  with open(file,'a', encoding='UTF-8') as f:
    f.write(re.sub(r'(\\033|)\[\d*m', '', "{} {}\n".format(get_prefix(type), log)))

# log a traceback from traceback.format_exc()
def logTraceback(error, silent=False):
  traceback = error.strip().split("\n")
  errorLogString = f'Execution excepted: {traceback[-1]}'
  tracebackFiles = []
  for file in (traceback):
    if "File \"/" in file:
      tracebackFiles.append("".join(" , ".join(file.split(", ")[0:2]).split('"')[1:]))
  
  # parse traceback files in a nice tree
  for i, file in enumerate(tracebackFiles):
    errorLogString += f'\n{" "*29}{"├" if i+1 < len(tracebackFiles) else "└"}─({colorLib.RED}{i}{colorLib.RESET}) {file}'
  
  log("critical", errorLogString, silent)

# log a message with colored prefixes
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
  
  # send the log to the log file
  logStripColor(logfile, type, message)

# run a query to get a value, using the same log format
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

# gets the prefix for a log type
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

# returns a styled progress bar given a list of items to create a progress bar for
def progress_bar(items, args):
  if args.verbose:
    return alive_it(items,title=get_prefix("info"), enrich_print=False, receipt=False, spinner=False, stats='(eta: {eta})')
  return items
