import re
import traceback

from heimdall.lib.utils.logger import logTraceback

from .logic import Logic


def postProcess(_line, signatures, events, constantStorage):
  # Cleaning up SHL that don't actually do anything
  _line = _line.replace(r' << 1 - 1', '')
  try:
    cleaned = _line
  except Exception as e:
    logTraceback(traceback.format_exc(), True)
  return cleaned

