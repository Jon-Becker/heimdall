import os
import re
import json
import traceback
import multiprocessing

from bidict import bidict

from ..io import *
from ..colors import colorLib
from ..apis.sigdir import resolve
from ..eth.classes.vm import VirtualMachine
from ..eth.classes.function import Function
from ..logger import log, logTraceback, progress_bar, logfile


# gets the history of a trace, -ith index
def traceHistory(trace, _i=0):
  return trace[-1*(_i+1)]

# finds all signatures by looking through the EVM dispatcher
def findSignatures(assembly, trace, args):
  signatures = []
  
  # finding the end of the function dispatcher
  for i in range(len(trace['trace'])):
    historical = traceHistory(trace['trace'], i)
    if historical['opcode'] == "JUMPI":
      endDispatcher = historical['inputs'][0]
      break
  
  # finding all PUSH4 instructions which occur before the end of the dispatcher
  for key in assembly:
    if key <= endDispatcher:
      if assembly[key]['opcode']['name'] == "PUSH4":
        if not assembly[key]['argument'] in signatures:
         signatures.append(assembly[key]['argument'])

  return [signatures, endDispatcher]

# main function for resolving functions
def resolveFunctions(assembly, args, output):
  try:
    functions = []
    log('info', f'Tracing EVM to determine function signatures...', True)
    
    # create a new VM instance with the disassembled target bytecode
    dispatcher = VirtualMachine(_assembly=assembly)
    dispatcherTrace = dispatcher.trace()
    
    # calculate the end of the dispatcher and all function signatures
    [signatures, endDispatcher] = findSignatures(assembly, dispatcherTrace, args)
    indicesDict = {}
    potentialDict = {}

    log('info', f'Found {colorLib.CYAN}{len(signatures)}{colorLib.RESET} unique signatures. Parsing functions...', True)
    log('info', f'Determining function entry points and resolving signatures...', True)
  
  except:
    
    # if theres an exception, we cant do anything since there were no found signatures. It could be a very
    # old compiler version or a compiler which doesnt use a dispatcher like Solidity, ex: Vyper.
    log('critical', f'Tracing EVM failed! Advanced logs available at {colorLib.RED + colorLib.UNDERLINE + logfile + colorLib.RESET}.')
    logTraceback(traceback.format_exc(), True)
    return

  # if the user wants to flush the cache, or if the cache doesnt exist, trace the signatures and cache some info about them
  if args.flush or args.ignore_cache or not pathExists(f'{output}/__cache__/indices.pickle') or not pathExists(f'{output}/__cache__/signatures.pickle'):
    
    # create a new function object with the signature, assembly, and the PC of the end of the dispatcher.
    # this will return a list of potential resolved function names
    for sig in progress_bar(signatures, args):
      function = Function(args, sig, assembly, endDispatcher)
      indicesDict[function.index] = sig
      potentialDict[sig] = function.potentialNames

    # write the cache fules
    makePath(f'{output}/__cache__')
    writeObj(f'{output}/__cache__/indices.pickle', indicesDict)
    writeObj(f'{output}/__cache__/signatures.pickle', potentialDict)
  else:
    
    # else, load the cache and save time
    log('info', 'Loaded signatures from cache!', True)
    indicesDict = loadFileAsPickle(f'{output}/__cache__/indices.pickle')
    potentialDict = loadFileAsPickle(f'{output}/__cache__/signatures.pickle')

  # convert the 1D indicesDict to a bidict
  indices = bidict(indicesDict)
  events = []
  mappings = []

  # for each function signature, create a new function object with some more information from the cache / resolved values
  # each object will be appended to a list of function objects for writing
  log('info', f'Determining function parameters, views, and returns...', True)
  for sig in progress_bar(signatures, args):
    try:
      function = Function(args, sig, assembly, endDispatcher, indices.inverse[sig], indices, potentialDict[sig])
      functions.append(function)
    except KeyError as e:
      
      # the signature failed to be resolved or found in cache
      pass
    except Exception as e:
      
      # encountered an unexpected error, log it and continue
      log('info', f'Ignoring signature {colorLib.CYAN}{hex(sig)}{colorLib.RESET}. Trace execution excepted!', True)
      logTraceback(traceback.format_exc(), True)
  
  # build the log output and save all mappings / event logs to a list for writing
  functionLogString = f'Determined return, typing, and parameters.'
  for i, f in enumerate(functions):
    functionLogString += (f'\n{" "*25}{"├" if i+1 < len(functions) else "└"}─({colorLib.CYAN}{i}{colorLib.RESET}) '
        f'{colorLib.CYAN}{f.name}{f.params} '
        f'{colorLib.RESET}{"external " if f.external else "public "}'
        f'{colorLib.RESET}{"" if f.external else "pure " if f.pure else "view " if f.view else ""}'
        f'{colorLib.RESET}{"payable " if f.payable else ""}'
        f'{f"returns({f.returns})" if f.returns else ""}'
        )
    
    # check if each event is unique, and insert it to the event list if it is
    for event in f.events:
      if not any(e['signature'] == event['signature'] for e in events):
        events.append(event)
      
    # check if each mapping is unique, and insert it to the mapping list if it is
    for mapping in f.mappings:
      if not any(m['slot'] == f.mappings[mapping]['slot'] for m in mappings):
        mappings.append(f.mappings[mapping])
  
  # log some info about the functions
  log('info', functionLogString, True)
  if all(func.view == True for func in functions):
    log('warning', 'No non-view functions found. Is this a proxy contract?', True)
  log('info', f'Found {colorLib.CYAN}{len(events)}{colorLib.RESET} unique events. Resolving signatures...', True)
  
  # if we are ignoring the cache or the cache doesnt exist, write the event logs to the cache
  if args.flush or args.ignore_cache or not pathExists(f'{output}/__cache__/events.pickle'):
    eventDict = {}
    
    # for each event, try to resolve it's signature on 4byte.directory
    for event in progress_bar(events, args):
      resolvedEvent = resolve(args, event['signature'][2:], 'event-signatures')
      if resolvedEvent:
        eventParams = re.search(r'\((.*)\)', resolvedEvent[0]).group(1).split(",")
        if '' in eventParams:
          eventParams.remove('')
        eventName = resolvedEvent[0].split("(")[0]
        eventDict[event['signature']] = {"name": eventName, "params": eventParams}
      else:
        
        # no match found, use a generic name. ex: event_ffffffff
        eventDict[event['signature']] = {"name": f'event_{event["signature"][2:10]}', "params": ["bytes" for i in range(event['topicCount']-1)]}
    
    # write the events to the cache
    writeObj(f'{output}/__cache__/events.pickle', eventDict)
    log('info', f'Resolved signature names.', True)
  else:
    
    # the cache file exists, load the events
    eventDict = loadFileAsPickle(f'{output}/__cache__/events.pickle')
  
  # building the abi
  abi = []
  abi.append({
      "type": "constructor",
      "inputs": [],
      "stateMutability": "nonpayable"
    })
  
  # write events to the abi
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
  
  # write functions to the abi, saving each constant storage value to a list
  constantStorage = {}
  for func in functions:
    if func.constant != False:
      constantStorage[func.name.replace('func_', 'storage_')] = func.constant
    abi.append({
      "type": "function",
      
      # if the function is a storage getter, change the default name to be more descriptive
      "name": func.name if not func.constant else func.name.replace('func_', 'storage_'),
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
    
  # write the abi to the output directory
  write(f'{output}/abi.json', json.dumps(abi, indent=2))
  log('success', f'Wrote ABI file {colorLib.GREEN}{output.replace(os.getcwd(), ".")}/abi.json{colorLib.RESET}')
    
  return [abi, functions, bidict(indicesDict), signatures, eventDict, constantStorage, mappings]