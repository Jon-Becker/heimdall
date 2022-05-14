import os
import importlib
import pathlib
from struct import pack

from ..utils.colors import colorLib
from ..utils.logger import log

def getModules(args=None):
  mods = []
  max_title_length = 0
  max_description_length = 0
  for item in os.listdir(pathlib.Path(__file__).parent.resolve()):
    if item.endswith('.py') and not "modules" in item and not "__init__" in item:
      try:
        temp = importlib.import_module(f'.lib.modules.{item.replace(".py", "")}', package='heimdall')
        meta = temp.meta
        meta['import'] = f'.lib.modules.{item.replace(".py", "")}'
        if len(meta['title']) >= max_title_length:
          max_title_length = len(meta['title'])
        if len(meta['description']) >= max_description_length:
          max_description_length = len(meta['description'])
        mods.append(meta)
      except Exception as e:
        log('warning', f'Module {colorLib.YELLOW}{item}{colorLib.RESET} failed to mount!')
        if args and args.verbose:
          log('warning', f'├─ {colorLib.YELLOW}{e.msg}{colorLib.RESET}')
          try:
            log('warning', f'└─({colorLib.GREY}{e.path}{colorLib.RESET})')
          except:
            pass
  return (mods, max_title_length, max_description_length)
