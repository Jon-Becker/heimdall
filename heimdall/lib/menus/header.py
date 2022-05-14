from ..utils.colors import colorLib
from ..utils.version import getLocalVersion

def getHeader():
  return (
    f'''{colorLib.BLUE}
 _   _  _____ ________  ________  ___   _      _     
| | | ||  ___|_   _|  \/  |  _  \/ _ \ | |    | |    
| |_| || |__   | | | .  . | | | / /_\ \| |    | |    
|  _  ||  __|  | | | |\/| | | | |  _  || |    | |    
| | | || |___ _| |_| |  | | |/ /| | | || |____| |____
\_| |_/\____/ \___/\_|  |_/___/ \_| |_/\_____/\_____/

{colorLib.RESET}Version:  {getLocalVersion()}
Author:   Jonathan Becker (jonathan@jbecker.dev)
GitHub:   https://github.com/Jon-Becker/heimdall

'''
  )