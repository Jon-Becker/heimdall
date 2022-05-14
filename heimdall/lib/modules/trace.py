import datetime

from timeit import default_timer as timer

from ..utils.logger import log

meta = {
  "title": "Trace",
  "description": "Trace the calls and events of a specific transaction",
  "author": "Jonathan Becker <jonathan@jbecker.dev>",
  "version": "v1.0.0",
}


def main(args):
  startTime = timer()
  
  print(args)

  endTime = timer()
  log('info', f'Operation completed in {datetime.timedelta(seconds=(endTime-startTime))}.\n')