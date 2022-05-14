import datetime
from alive_progress import alive_it

from .colors import colorLib

def log(type, message):
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

  print(datetime.datetime.now().strftime(f'[{accent}%H:%M:%S.%f{colorLib.RESET}] [{accent}{type.upper()}{colorLib.RESET}] {message}'))

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
