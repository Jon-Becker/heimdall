import os
import importlib

from ..modules.modules import getModules
from ..utils.colors import colorLib
from ..utils.version import getLocalVersion

def getHelp():
  
  modules = []
  fetched_modules = getModules()
  nl = "\n"
  
  modules.append(f'{colorLib.UNDERLINE}{colorLib.BOLD}{"#".rjust(9)}  |{"Name".rjust(fetched_modules[1]+2)}  |{"Description".rjust(fetched_modules[2]+2)}    {colorLib.RESET}')
  modules.append(f'{"".rjust(9)}  |{"".rjust(fetched_modules[1]+2)}  |{"".rjust(fetched_modules[2]+2)}')
  for item in fetched_modules[0]:
    modules.append(f'{str(len(modules)-2).rjust(9)}  |{item["title"].rjust(fetched_modules[1]+2)}  |{item["description"].rjust(fetched_modules[2]+2)}')
  
  return (
    f'''Usage: {colorLib.BOLD}heimdall [-m/--module] MODULE [-t/--target] VALUE [-o path] [-n value]
                                     [-p value] [-p value] [--redeploy]
                                     [--beautify] [--version] [--update]
                                     [-v] [-h] [--redeploy] [--beautify]{colorLib.RESET}

Powerful Ethereum smart contract toolkit for forensics, manipulation, and research.

Options:
  -h, --help                          Show the help message and exit
  -hh                                 Show advanced help message and exit
  --version                           Display version information and exit
  --update                            Updates heimdall to the latest release
  -v, --verbose                       Toggle verbose output

  Modules:
    Below is a list of modules currently supported on Heimdall

{nl.join(str(x) for x in modules)}

  Parameters:
    -m MODULE, --module MODULE        Operation module, either name or number from list
    -t TARGET, --target TARGET        Target of operation (file, transaction id,
                                        or address)
    -o PATH, --output PATH            Path to write output to
    -c ID, --chain ID                 Chain ID of target
    -p URL, --provider URL            URL of custom Ethereum provider

  Additional:
    --open, --edit                    Attempts to open nano / edit on the operation
    --redeploy ID                     Redeploys the contract from -n onto ID
    --beautify                        Attempts to beautify the downloaded contract using
                                        statistical renaming and spacing
    --default                         Always use defaults when prompted for input
    --flush, --ignore-cache           Flushes the cache and rewrites it
'''
  )