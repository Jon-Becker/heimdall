import os

from heimdall.lib.utils.io import write_config_value_at_path
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
  config = getConfig()
  log('info', f'Heimdall configuration is located at: {colorLib.UNDERLINE+colorLib.CYAN+ configPath +colorLib.RESET} .')
  
  # handling for editing the config file in nano or edit
  if not args.open and not args.default:
    editFile = query('info', 'N', 'Would you like to edit the configuration file? (y/N):')
  elif args.default:
    editFile = "n"
    log('info', 'Would you like to edit the configuration file? (y/N): N')
  if args.open or editFile.lower() == "y":
    if os.name not in ('nt', 'dos'):
      os.system(f'nano {configPath}')
    else:
      os.system(f'edit {configPath}')
      
  # if they want to toggle autoupdate, set it in config
  if args.autoupdate:
    write_config_value_at_path(getConfigPath(), 'autoupdate', not getConfig()['autoupdate'])
    log('info', f"PyPi autoupdating is set to: {colorLib.CYAN}{'true' if getConfig()['autoupdate'] else 'false'}{colorLib.RESET}")