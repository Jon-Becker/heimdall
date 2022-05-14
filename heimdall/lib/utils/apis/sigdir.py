import os
import json
import requests

from ..logger import log
from ..colors import colorLib

def resolve(args, signature, type="signatures"):
  try:
    sigRequest = requests.get(f'https://www.4byte.directory/api/v1/{type}/?format=json&hex_signature=0x{signature}', timeout=3)
    if sigRequest.status_code == 200:
      sigBody = json.loads(sigRequest.text)
      if len(sigBody['results']) > 0:

        textSignatures = []
        for sig in sigBody['results']:
          textSignatures.append(sig["text_signature"])

        return textSignatures

    else:
      return None
  except:
    return None
