import os
import sys
import platform
import argparse
import pathlib
import datetime
import importlib
import traceback

from timeit import default_timer as timer

from .lib.utils.io import checksum, delete
from .lib.menus.help import getHelp
from .lib.utils.colors import colorLib
from .lib.menus.header import getHeader
from .lib.modules.modules import getModules
from .lib.utils.logger import log, logTraceback, logfile, purgeOldLogfiles
from .lib.utils.version import getLocalVersion, checkVersionUpToDate, update

def main(argv=None):
  
  # clear screen and print header
  purgeOldLogfiles()
  command = 'clear'
  if os.name in ('nt', 'dos'):
      command = 'cls'
  os.system(command)
  print(getHeader())
  
  heimdall = argparse.ArgumentParser(prog='heimdall', usage='heimdall [options]', add_help=False)

  # variable arguments
  heimdall.add_argument('-m', '--module', help="Operation module")
  heimdall.add_argument('-t', '--target', help="Operation target")
  heimdall.add_argument('-o', '--output', help="Path to write output to")
  heimdall.add_argument('-c', '--chain', help="Chain ID of target network")
  heimdall.add_argument('-p', '--provider', help="Custom provider URL")
  heimdall.add_argument('--indent', help="Sets the indent level for output files (Default 2)")
  heimdall.add_argument('--redeploy', help="Redeploy contract")

  # toggleable arguments
  heimdall.add_argument('-v', '--verbose', help="Use verbose mode", action="store_true")
  heimdall.add_argument('-h', '--help', help="Show the help menu", action="store_true")
  heimdall.add_argument('--version', help="Display version information", action="store_true")
  heimdall.add_argument('--update', help="Update heimdall to latest release", action="store_true")
  heimdall.add_argument('--beautify', help="Beautify contract, using statistical renaming", action="store_true")
  heimdall.add_argument('--default', help="Always use defaults when prompted for input", action="store_true")
  heimdall.add_argument('--flush', help="Flushes the cache", action="store_true")
  heimdall.add_argument('--autoupdate', help="Toggle autoupdates", action="store_true")
  heimdall.add_argument('--ignore-cache', help="Ignores the cache (SLOWER!)", action="store_true")
  heimdall.add_argument('--open', '--edit', help="Attempts to open nano / edit on the operation", action="store_true")  

  # parse arguments
  (args, extras) = heimdall.parse_known_args()
  
  # if theres an extra argument, it's assumed to be the module.
  # this will allow commands like `heimdall config` instead of `heimdall -m config`
  if len(extras) == 1:
    args.__setattr__('module', extras[0])
  
  log('debug', " ".join(sys.argv), True)
  log('debug', f'Uname: {platform.uname()}', True)
  log('debug', f'Checksum: {checksum(f"{pathlib.Path(__file__).parent.resolve()}/lib")}', True)
  log('debug', f'Heimdall Version: {getLocalVersion()}', True)
  
  startTime = timer()
  try:
    if args.help:
      print(getHelp())
      delete(logfile)
    else:
      if args.module:
        handled = False

        # get the selected module
        available_modules = getModules(args)
        if args.module.lower().isdigit() and (int(args.module) <= len(available_modules[0])-1):
          selected_module = importlib.import_module(available_modules[0][int(args.module)]['import'], package='heimdall')
          handled = True
        else:
          for module in available_modules[0]:
            if args.module.lower() == module["title"].lower():
              selected_module = importlib.import_module(module['import'], package='heimdall')
              handled = True
              break
        if not handled:
          log('critical', f'Module {colorLib.RED}{args.module}{colorLib.RESET} not found. Use -h to show the help menu.')
          
        # run the selected module
        try:
          log('debug', f'{selected_module.meta["title"]} ({selected_module.meta["version"]})', True)
          selected_module.main(args)
        except Exception as e:
          logTraceback(traceback.format_exc(), True)
          log('critical', f'Execution failed! Advanced logs available at {colorLib.RED + colorLib.UNDERLINE + logfile + colorLib.RESET} .')
                
        # run version check after module execution to minimize startup time 
        # from command send -> first log
        version = checkVersionUpToDate()
        if not version[0]:
          log('alert', f'This version of Heimdall is outdated!')
          update(version)
      else:
        log('critical', f'Missing a mandatory argument (-m or --module). Use -h to show the help menu.')
        delete(logfile)
        sys.exit(0)
    
      endTime = timer()
      log('info', f'Operation completed in {datetime.timedelta(seconds=(endTime-startTime))}.')
      if args.module in ('debug', 'config', 'publish'):
        delete(logfile)
    
  except KeyboardInterrupt:
    endTime = timer()
    log('critical', f'Operation aborted after {datetime.timedelta(seconds=(endTime-startTime))}.\n')
    sys.exit(0)
  
  except:
    logTraceback(traceback.format_exc(), True)
    sys.exit(0)
  
if __name__ == '__main__':
  sys.exit(main(sys.argv))