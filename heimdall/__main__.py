import os
import sys
import argparse
import pathlib
import datetime
import importlib
import traceback

from timeit import default_timer as timer

from .lib.utils.io import checksum
from .lib.menus.help import getHelp
from .lib.utils.colors import colorLib
from .lib.menus.header import getHeader
from .lib.modules.modules import getModules
from .lib.utils.logger import log, logTraceback, logfile
from .lib.utils.version import getLocalVersion, checkVersionUpToDate, update

def main(argv=None):
  command = 'clear'
  if os.name in ('nt', 'dos'):
      command = 'cls'
  os.system(command)
  print(getHeader())
  
  heimdall = argparse.ArgumentParser(prog='heimdall', usage='heimdall [options]', add_help=False)

  heimdall.add_argument('-m', '--module', help="Operation module")
  heimdall.add_argument('-t', '--target', help="Operation target")
  heimdall.add_argument('-o', '--output', help="Path to write output to")
  heimdall.add_argument('-c', '--chain', help="Chain ID of target network")
  heimdall.add_argument('-p', '--provider', help="Custom provider URL")
  heimdall.add_argument('--redeploy', help="Redeploy contract")

  heimdall.add_argument('-v', '--verbose', help="Use verbose mode", action="store_true")
  heimdall.add_argument('-h', '--help', help="Show the help menu", action="store_true")
  heimdall.add_argument('--version', help="Display version information", action="store_true")
  heimdall.add_argument('--update', help="Update heimdall to latest release", action="store_true")
  heimdall.add_argument('--beautify', help="Beautify contract, using statistical renaming", action="store_true")
  heimdall.add_argument('--default', help="Always use defaults when prompted for input", action="store_true")
  heimdall.add_argument('--flush', help="Flushes the cache", action="store_true")
  heimdall.add_argument('--ignore-cache', help="Ignores the cache (SLOWER!)", action="store_true")
  heimdall.add_argument('--open', '--edit', help="Attempts to open nano / edit on the operation", action="store_true")  

  (args, extras) = heimdall.parse_known_args()

  for ext in extras:
    try:
      if '=' in ext:
        args.__setattr__(ext.split('=')[0], ext.split('=')[1])
      else:
        args.__setattr__(ext, True)
    except: pass
  
  log('debug', " ".join(sys.argv), args.module != 'debug')
  log('debug', f'Machine: {" ".join(os.uname().version.split(" ")[0:4])} {os.uname().version.split(" ")[11]}', args.module != 'debug')
  log('debug', f'Checksum: {checksum(f"{pathlib.Path(__file__).parent.resolve()}/lib")}', args.module != 'debug')
  log('debug', f'Heimdall Version: {getLocalVersion()}', args.module != 'debug')
  
  try:
    if args.help:
      print(getHelp())
    
    else:
      if args.module:
        handled = False
        startTime = timer()

        available_modules = getModules(args)
        if args.module.lower().isdigit() and (int(args.module) <= len(available_modules[0])-1):
          selected_module = importlib.import_module(available_modules[0][int(args.module)]['import'], package='heimdall')
          handled = True
          try:
            log('debug', f'{selected_module.meta["title"]} module version: {selected_module.meta["version"]}', True)
            selected_module.main(args)
          except Exception as e:
            logTraceback(traceback.format_exc())
            log('critical', f'Execution failed! Advanced logs available at {colorLib.RED + colorLib.UNDERLINE + logfile + colorLib.RESET} .')
        else:
          for module in available_modules[0]:
            if args.module.lower() == module["title"].lower():
              selected_module = importlib.import_module(module['import'], package='heimdall')
              handled = True
              try:
                log('debug', f'{selected_module.meta["title"]} module version: {selected_module.meta["version"]}', True)
                selected_module.main(args)
              except Exception as e:
                logTraceback(traceback.format_exc())
                log('critical', f'Execution failed! Advanced logs available at {colorLib.RED + colorLib.UNDERLINE + logfile + colorLib.RESET} .')
          
          if not handled:
            print(f'heimdall: error: Module {colorLib.YELLOW}{args.module}{colorLib.RESET} not found. Use -h to show the help menu.\n')
        
        version = checkVersionUpToDate()
        if not version[0]:
          log('alert', f'This version of Heimdall is outdated!')
          update(version)
              
        endTime = timer()
        log('info', f'Operation completed in {datetime.timedelta(seconds=(endTime-startTime))}.\n')
      else:
        print('heimdall: error: Missing a mandatory option (-m or --module). Use -h to show the help menu.\n')
  except KeyboardInterrupt:
    endTime = timer()
    log('critical', f'Operation aborted after {datetime.timedelta(seconds=(endTime-startTime))}.\n')
    sys.exit(0)
  
if __name__ == '__main__':
  sys.exit(main(sys.argv))