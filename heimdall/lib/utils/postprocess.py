import re
import traceback

from .logic import Logic


def postProcess(_line, signatures, events, constantStorage):
  # Cleaning up SHL that don't actually do anything
  _line = _line.replace(r' << 1 - 1', '')
  try:
    cleaned = _line
    
    # Replace all Event_0x00000000 with resolved event name
    eventPlaceholder = re.findall(r'Event_0x[a-fA-F0-9]{8}', cleaned, re.IGNORECASE)
    if len(eventPlaceholder) >= 1:
      placeholderSignature = eventPlaceholder[0][6:16]
      for eventSignature in events:
        if eventSignature.startswith(placeholderSignature):
          cleaned = cleaned.replace(eventPlaceholder[0], events[eventSignature]['name'])
    
    # Replace all constant SLOADS with their names
    storage = re.findall(r'LOAD\{[0-9]{0,3}\}', cleaned, re.IGNORECASE)
    for i, access in enumerate(storage):
      access = access.replace("LOAD{", "").replace("}", "")
      handled = False
      for key in constantStorage:
        if constantStorage[key] == int(access):
          cleaned = cleaned.replace(storage[i], f'_{key}')
          handled = True
          break
      if not handled:
        cleaned = cleaned.replace(storage[i], f'storage[{access}]')
      
    try:
      # Replace all masks with type casting
      casting = re.findall(r'MASK{.*?}', cleaned, re.IGNORECASE)
      for i, cast in enumerate(casting):
        mask = 0
        cast = cast.replace("MASK{", "").replace("}", "")
        temp = cast
        argArray = cast.split(" & ")
        
        # TODO: fix casting detection
        if argArray[0].isnumeric():
          mask = int(argArray[0])
          temp = argArray[1]
        elif argArray[1].isnumeric():
          mask = int(argArray[1])
          temp = argArray[0]
        else:
          for j, arg in enumerate(argArray):
            try:
              mask = eval(arg)
              if type(mask) == int:
                temp = argArray[1 if j == 0 else 0]
                break
            except:
              pass
            
        if mask != 0:
          temp = f'{Logic.resolveMask({"val": (len(hex(mask)[2:])*4), "isPointer": False})[0]}({temp})'
        
        cleaned = cleaned.replace(casting[i], temp)
    except:
      pass
  except Exception as e:
    pass
  return cleaned

