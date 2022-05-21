import os
from ..config import *
from ..utils.logger import *
from ..utils.colors import colorLib

meta = {
  "title": "Config",
  "description": "Easily modify the configuration on Heimdall",
  "author": "Jonathan Becker <jonathan@jbecker.dev>",
  "version": "v1.0.0",
}

def main(args):
  configPath = getConfigPath()
  log('info', f'Heimdall configuration is located at: {colorLib.UNDERLINE+colorLib.CYAN+ configPath +colorLib.RESET}.')
  
  if not args.open:
    editFile = query('info', 'N', 'Would you like to edit the configuration file? (y/N):')
    
  if editFile.lower() == "y" or args.open:
    if os.name == 'posix':
      os.system(f'nano {configPath}')
    else:
      os.system(f'edit {configPath}')