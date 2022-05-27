import os
import hashlib
from ..config import *
from ..utils.logger import *
from ..utils.colors import colorLib

meta = {
  "title": "Debug",
  "description": "Easily access Heimdall debug information",
  "author": "Jonathan Becker <jonathan@jbecker.dev>",
  "version": "v1.0.0",
}
 
# simply gets the most recent log file and gets its path
def main(args):
  max = 0
  for item in os.listdir(f'{pathlib.Path(__file__).parent.parent.parent.resolve()}/logs'):
    if "__" not in item and int(item.split("-")[1].replace(".log", "")) > max and item not in logfile:
      max = int(item.split("-")[1].replace(".log", ""))
  log('debug', f'Latest log file available at: {colorLib.UNDERLINE+colorLib.CYAN}{pathlib.Path(__file__).parent.parent.parent.resolve()}/logs/heimdall-{max}.log{colorLib.RESET} .')