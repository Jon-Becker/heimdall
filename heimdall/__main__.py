import argparse
import datetime
from inspect import trace
import os
import sys
import importlib
import traceback


from timeit import default_timer as timer

from .lib.modules.modules import getModules
from .lib.utils.colors import colorLib
from .lib.menus.header import getHeader
from .lib.menus.help import getHelp
from .lib.utils.logger import log
from .lib.utils.version import getRemoteVersion, getLocalVersion

def main(argv=None):
  command = 'clear'
  if os.name in ('nt', 'dos'):
      command = 'cls'
  os.system(command)
  print(getHeader())
  
  if getRemoteVersion() != getLocalVersion():
    log('alert', f'This version of Heimdall is outdated!')
    log('alert', f'You can update to version {colorLib.GREEN}{getRemoteVersion()}{colorLib.RESET} by running: {colorLib.GREEN}pip install eth-heimdall --upgrade{colorLib.RESET} !')
    print()

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

  args = heimdall.parse_args()
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
            selected_module.main(args)
          except Exception as e:
            traceback.print_exc()
            log('critical', f'Execution failed! Advanced logs available.')
        else:
          for module in available_modules[0]:
            if args.module.lower() == module["title"].lower():
              selected_module = importlib.import_module(module['import'], package='heimdall')
              handled = True
              try:
                selected_module.main(args)
              except Exception as e:
                traceback.print_exc()
                log('critical', f'Execution failed! Advanced logs available.')
          
          if not handled:
            print(f'heimdall: error: Module {colorLib.YELLOW}{args.module}{colorLib.RESET} not found. Use -h to show the help menu.\n')

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