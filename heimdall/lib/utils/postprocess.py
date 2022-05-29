import re
import traceback

from heimdall.lib.utils.logger import logTraceback

from .logic import Logic


def postProcess(_line, signatures, events, constantStorage):
  
  # cleaning up logic that doesn't actually do anything
  _line = re.sub(r'( << 1 - 1|\/ 1|0 + | + 0)', '', _line)

  # cleaning up redundant castings
  
  try:
    cleaned = _line
    
    # replace all Event_0x00000000 with resolved event name
    eventPlaceholder = re.findall(r'Event_0x[a-fA-F0-9]{8}', cleaned, re.IGNORECASE)
    if len(eventPlaceholder) >= 1:
      placeholderSignature = eventPlaceholder[0][6:16]
      for eventSignature in events:
        if eventSignature.startswith(placeholderSignature):
          cleaned = cleaned.replace(eventPlaceholder[0], events[eventSignature]['name'])
    
    # replace all constant SLOADS with their names
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
        cleaned = cleaned.replace(storage[i], f'_storage_{hex(int(access))}')
        
  except Exception as e:
    logTraceback(traceback.format_exc(), True)
  return cleaned

