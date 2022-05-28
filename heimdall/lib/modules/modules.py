from hashlib import md5
import json
import os
import importlib
import pathlib
import traceback

from heimdall.lib.utils.io import write

from ..utils.colors import colorLib
from ..utils.logger import log, logTraceback

def getModules(args=None):
  mods = []
  dist = []
  max_title_length = 0
  max_description_length = 0
  
  # get all modules in heimdall/lib/modules
  for item in os.listdir(pathlib.Path(__file__).parent.resolve()):
    if item.endswith('.py') and not "modules" in item and not "__init__" in item:
      try:
        # import the module to get the meta data
        temp = importlib.import_module(f'.lib.modules.{item.replace(".py", "")}', package='heimdall')
        meta = temp.meta
        meta['import'] = f'.lib.modules.{item.replace(".py", "")}'
        
        # store max lens for help menu formatting
        if len(meta['title']) >= max_title_length:
          max_title_length = len(meta['title'])
        if len(meta['description']) >= max_description_length:
          max_description_length = len(meta['description'])
          
        # add the module to the dist
        mods.append(meta)
        dist.append({
          "name": meta['title'],
          "version": meta['version'],
          "checksum": md5(open(f'{pathlib.Path(__file__).parent.resolve()}/{item}' ,'rb').read()).hexdigest()
        })
      except Exception as e:
        
        # if a module fails to mount, log the error and continue to other modules
        log('warning', f'Module {colorLib.YELLOW}{item}{colorLib.RESET} failed to mount!')
        logTraceback(traceback.format_exc(), True)
  
  # write the hashsums to the dist file, will be used when we have a package manager
  write(f'{pathlib.Path(__file__).parent.resolve()}/dist.json', json.dumps(dist, indent=4))
  return (mods, max_title_length, max_description_length)