from encodings import utf_8
import json
import datetime
import os
import pickle
import re
import traceback

from bidict import bidict
from ...config import loadFileAsPickle
from ..apis.sigdir import resolve

from ..logger import log, progress_bar
from ..io import makePath, outputDirectory, write, pathExists, writeObj
from ..colors import colorLib
from ..eth.classes.vm import VirtualMachine
from ..eth.classes.function import Function

def traceHistory(trace, _i=0):
  return trace[-1*(_i+1)]
def findSignatures(assembly, trace, args):
  signatures = []
  for i in range(len(trace['trace'])):
    historical = traceHistory(trace['trace'], i)
    if historical['opcode'] == "JUMPI":
      endDispatcher = historical['inputs'][0]
      break
  
  for key in assembly:
    if key <= endDispatcher:
      if assembly[key]['opcode']['name'] == "PUSH4":
        if not assembly[key]['argument'] in signatures:
         signatures.append(assembly[key]['argument'])
  
  return [signatures, endDispatcher]
def resolveFunctions(assembly, args, output):
  try:
    functions = []
    if args.verbose:
      log('info', f'Tracing EVM to determine function signatures...')

    dispatcher = VirtualMachine(_assembly=assembly)
    dispatcherTrace = dispatcher.trace()
    [signatures, endDispatcher] = findSignatures(assembly, dispatcherTrace, args)
    indicesDict = {}
    potentialDict = {}

    if args.verbose:
      log('info', f'Found {colorLib.CYAN}{len(signatures)}{colorLib.RESET} unique signatures. Parsing functions...')
      log('info', f'Determining function entry points and resolving signatures...')
  except:
    log('critical', f'Tracing EVM failed! Verbose logs saved to {colorLib.CYAN}{output.replace(os.getcwd(), ".")}/{datetime.date.today().strftime("%m-%d-%Y")}.log{colorLib.RESET}')
    return

  if args.flush or args.ignore_cache or not pathExists(f'{output}/__cache__/indices.hc') or not pathExists(f'{output}/__cache__/signatures.hc'):
    for sig in progress_bar(signatures, args):
      function = Function(args, sig, assembly, endDispatcher)
      indicesDict[function.index] = sig
      potentialDict[sig] = function.potentialNames

    makePath(f'{output}/__cache__')
    writeObj(f'{output}/__cache__/indices.hc', indicesDict)
    writeObj(f'{output}/__cache__/signatures.hc', potentialDict)
  else:
    if args.verbose:
      log('info', 'Loaded signatures from cache!')
    indicesDict = loadFileAsPickle(f'{output}/__cache__/indices.hc')
    potentialDict = loadFileAsPickle(f'{output}/__cache__/signatures.hc')

  indices = bidict(indicesDict)
  events = []
  mappings = []

  if args.verbose:
    log('info', f'Determining function parameters, views, and returns...')
  for sig in progress_bar(signatures, args):
    try:
      function = Function(args, sig, assembly, endDispatcher, indices.inverse[sig], indices, potentialDict[sig])
      functions.append(function)
    except KeyError as e:
      pass
    except Exception as e:
      if args.verbose:
        traceback.print_exc()
        log('info', f'Ignoring signature {colorLib.CYAN}{hex(sig)}{colorLib.RESET}. Trace execution excepted!')
    
  if args.verbose:
    functionLogString = f'Determined return, typing, and parameters.';

    for i, f in enumerate(functions):
      #TODO: these can be made into any() funcs
      for event in f.events:
        unique = True
        for e in events:
          if e['signature'] == event['signature']:
            unique = False
            break
            
        if unique:
          events.append(event)
          
      for mapping in f.mappings:
        unique = True
        for map in mappings:
          if map['slot'] == f.mappings[mapping]['slot']:
            unique = False
            break
            
        
        if unique:
          mappings.append(f.mappings[mapping])
      
      functionLogString += (f'\n{" "*25}{"├" if i+1 < len(functions) else "└"}─({colorLib.CYAN}{i}{colorLib.RESET}) '
          f'{colorLib.CYAN}{f.name}{f.params} '
          f'{colorLib.RESET}{"external " if f.external else "public "}'
          f'{colorLib.RESET}{"" if f.external else "pure " if f.pure else "view " if f.view else ""}'
          f'{colorLib.RESET}{"payable " if f.payable else ""}'
          f'{f"returns({f.returns})" if f.returns else ""}'
         )
    log('info', functionLogString)
    
    if all(func.view == True for func in functions):
      log('warning', 'No non-view functions found. Is this a proxy contract?')

    log('info', f'Found {colorLib.CYAN}{len(events)}{colorLib.RESET} unique events. Resolving signatures...')
  
  if args.flush or args.ignore_cache or not pathExists(f'{output}/__cache__/events.hc'):
    eventDict = {}
    for event in progress_bar(events, args):
      resolvedEvent = resolve(args, event['signature'][2:], 'event-signatures')
      if resolvedEvent:
        eventParams = re.search(r'\((.*)\)', resolvedEvent[0]).group(1).split(",")
        if '' in eventParams:
          eventParams.remove('')
        eventName = resolvedEvent[0].split("(")[0]
        eventDict[event['signature']] = {"name": eventName, "params": eventParams}
      else:
        eventDict[event['signature']] = {"name": f'event_{event["signature"][2:10]}', "params": ["bytes" for i in range(event['topicCount']-1)]}
        
    writeObj(f'{output}/__cache__/events.hc', eventDict)
    
    if args.verbose:
      log('info', f'Resolved signature names.')
  else:
    eventDict = loadFileAsPickle(f'{output}/__cache__/events.hc')
  
  abi = []
  abi.append({
      "type": "constructor",
      "inputs": [],
      "stateMutability": "nonpayable"
    })
  for key in eventDict:
    abi.append({
      "type": "event",
      "name": eventDict[key]['name'],
      "inputs": [{
        "name": f'arg{index}',
        "internalType": input,
        "type": input
        } for index, input in enumerate(eventDict[key]['params'])],
    })
  
  constantStorage = {}
  for func in functions:
    if func.constant != False:
      constantStorage[func.name] = func.constant
    abi.append({
      "type": "function",
      "name": func.name,
      "inputs": [{
        "name": f'arg{index}',
        "internalType": input,
        "type": input
        } for index, input in enumerate(func.params)],
      "outputs": [{
        "name": f'ret0',
        "internalType": func.returns.replace(" memory", ""),
        "type": func.returns.replace(" memory", ""),
        }] if func.returns else [],
      "stateMutability": "payable" if func.payable else 
                          "nonpayable" if func.external else
                          "pure" if func.pure else 
                          "view" if func.view else 
                          "nonpayable",
      "constant": True if func.constant != False else False
    })
  write(f'{output}/abi.json', json.dumps(abi, indent=2))
  log('success', f'Wrote ABI file {colorLib.GREEN}{output.replace(os.getcwd(), ".")}/abi.json{colorLib.RESET}')
    
  return [abi, functions, bidict(indicesDict), signatures, eventDict, constantStorage, mappings]