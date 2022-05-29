from copy import deepcopy
import re
import traceback
from web3 import Web3

from ...logic import Any, Logic, _match, bytesToType, commonTypes, determineType, solidify_wrapped, offsetToMemoryName, solidify
from ...apis.sigdir import resolve
from ...eth.classes.vm import VirtualMachine
from ...eth.classes.stack import Stack
from ...logger import log, logTraceback, query
from ...colors import colorLib

class Function():
  
  # initialize a new function object with some default information
  def __init__(self, args, signature, assembly, endDispatcher, index=None, indices=None, potentialNames=None, params=None):
    self.args = args
    self.event_signatures = []
    self.events = []
    self.signature = Logic.padHex(None, signature, 8)
    self.name = None
    self.assembly = assembly
    self.potentialNames = potentialNames if potentialNames != None else resolve(args, self.signature[2:])
    self.endDispatcher = endDispatcher
    self.index = index if index != None else self.getEntryPoint()
    self.indices = indices
    self.returns = None
    self.external = False
    self.view = True
    self.pure = True
    self.payable = True
    self.constant = False
    self.logic = []
    self.warnings = []    
    self.memory = {}
    self.memlast = {}
    self.mappings = {}
    self.storage = None
    
    if self.indices != None:
      self.params = params if params != None else self.resolveParams()
  
  # determines if the jumpdest is a jump to another function
  # ( I think this could be somehow used to find internal functions, dont quote me on that )
  def isFunctionCall(self, dest):
    return dest if (dest in [item for sublist in self.indices.keys() for item in sublist]) else None

  # determines the entry point of the function
  def getEntryPoint(self):
    
    # create a new VM with the disassembly of the target bytecode
    vm = deepcopy(VirtualMachine(_assembly=self.assembly, _calldata=int(self.signature, 16)))
   
   # recursively make a tree of all jumpdests and their conditions
    def resolve(entries=[], logJump=False):
      try:
        
        # get the next instruction and execute it on the VM
        instructionIndex = list(self.assembly.keys()).index(vm.instruction)
        code = self.assembly[vm.instruction]
        lastPC = vm.instruction
        vm.lastInstruction = lastPC
        vm.instruction = (list(self.assembly.keys())[instructionIndex+1])
        if vm.instruction > self.endDispatcher:
          return tuple(entries)
        vm.execute(code['opcode']['name'], code['argument'])
        call = vm.stacktrace[-1]
        
        # if the instruction is a push4 and the value matches the signature, we have found an entry point  
        if call['opcode'] == "PUSH4" and call['outputs'] == int(self.signature, 16):
          return resolve(entries, True)
        
        # if we already found an entry point, get the value of the jumpdest. This is the entry point for the function
        if logJump and code['opcode']['name'] in ['JUMP', 'JUMPI']:
          if call['outputs']:
            entries.append(call['outputs'])
          else:
            if call['inputs']:
              entries.append(call['inputs'][0])
            else:
              entries.append(vm.stacktrace[-2]['outputs'])
          return resolve(entries, False)
        return resolve(entries, logJump)
      
      except Exception as e:
        log('warning', 'Exception encountered when resolving function index.', not self.args.verbose)
        logTraceback(traceback.format_exc(), True)
        
    return resolve()
  
  
  def resolveParams(self):
    def trace(calldata, startPoint=1, stack=Stack(), stacktrace=[], handled=[]):
      
      # create a new VM object with a set of arguments which can come from the recursive tree
      vm = deepcopy(VirtualMachine(_assembly=self.assembly, _calldata=calldata, _instruction=startPoint, _stack=stack, _stacktrace=stacktrace))
      
      def map(mapping=[], getMask=False):
        
        # get the next instruction and execute it on the VM
        find_cd_mask = getMask
        instructionIndex = list(self.assembly.keys()).index(vm.instruction)
        code = self.assembly[vm.instruction]
        lastPC = vm.instruction
        vm.lastInstruction = lastPC
        vm.instruction = (list(self.assembly.keys())[instructionIndex+1])
        next = (list(self.assembly.keys())[instructionIndex+1])
        ret = vm.execute(code['opcode']['name'], code['argument'])
        call = vm.stacktrace[-1]
        
        # if the instruction executed after the dispatcher, it's part of the function logic 
        if call['pc'] > self.endDispatcher:
          
          # if the instruction is a state reading instruction, it's no longer a pure function
          if call['opcode'] in ['SSTORE', 'SLOAD', 'DELEGATECALL', 'STATICCALL', 'CALL', 'CALLCODE']:
            self.pure = False
            
            # convert all SLOAD operations to a value and store it
            if call['opcode'] == "SLOAD":
              self.storage = solidify_wrapped(call["wrapped"], vm, self)
            
            # if we are storing a value, add the store logic to the decompiled contract
            elif call['opcode'] == "SSTORE":
              key = solidify_wrapped(("SLOAD", Any, call['wrapped'][0]), vm, self)
              value = solidify_wrapped(call["wrapped"][1:], vm, self)
                  
              # appending logic
              self.logic.append([call['pc'], f'{key} = {value};'])
              self.view = False

            else:
              
              # handling for external contract calls
              callParameters = call['inputs']
              # if delegatecall or staticcall, insert an empty value field
              if call['opcode'] in ('STATICCALL', 'DELEGATECALL'):
                callParameters.insert(2, 0)
                
              # get and add all sources for the external call to the solidity logic
              source = solidify_wrapped(call['wrapped'][1], vm, self)
              self.logic.append([call['pc'], f'bytes memory {source} = {self.memory[source]["value"]};'])
              
              # I'm sorry this is extremely ugly, we just have to actually parse these 
              # callParameters into a solidity staticcall, and I dont want a massive fstring
              # so I broke it up a bit into parts
              self.logic.append([call['pc'] ,(
                f'(bool success, bytes{callParameters[6]} memory {offsetToMemoryName(callParameters[5])}) =' 
                f' address({source}).staticcall'
                f'({offsetToMemoryName(callParameters[3])});'
              )])
              
              # this is no longer a view function since it modifies the state
              self.view = False
          
          # if the instruction is an external call, add an external tag to this function object
          if call['opcode'] in ['DELEGATECALL', 'STATICCALL', 'CALL']:
            self.external = True

          # save all memory storages to the decompiled contract
          if call['opcode'] in ['MSTORE', 'MSTORE8']:
            try:
              self.memlast[offsetToMemoryName(call["inputs"][0])] = self.memory[offsetToMemoryName(call["inputs"][0])]
            except:
              pass
            self.memory[offsetToMemoryName(call["inputs"][0])] = {
              "value": solidify_wrapped(call["wrapped"][1:], vm, self),
              "pc": call['pc']
            }

          # add all event emissions to the decompiled contract
          if 'LOG' in call['opcode']:
            
            # add all sources for the external call to the solidity logic
            sources = []
            for temp in call['wrapped']:
              sources.append(str(solidify_wrapped(temp, vm, self)))
            sources += call['event']['topics']['unindexed']
            [self.logic.append([call['pc'], f'bytes memory {source} = {self.memory[source]["value"]};']) for source in sources if re.match(r"var[0-9]*", source)]
            
            # add the event to the decompiled contract
            self.logic.append([call['pc'], f'emit Event_{call["event"]["signature"][:10]}({", ".join(sources)});'])

          # logic for calldataloads and determining function types
          if 'wrapped' in call and call['wrapped'] != None:
            
            # if the opcode is an AND, it's typically a masking operation and we can calculate the type with the mask value
            if call['opcode'] == "AND" and (
              (m := _match(call['wrapped'], [(':offset', 0, 'CALLDATALOAD'), (None, ':mask', Any)])) or 
              (m := _match(call['wrapped'], [(None, ':mask', Any), (':offset', 0, 'CALLDATALOAD')]))
            ):
              mapping.append([ (len(hex(m.mask)[2:])*4) , m.offset ])
            
            # if the opcode is a ISZERO, it's typically a boolean
            elif call['opcode'] == 'ISZERO':
              if(m := _match(call['wrapped'], [(':offset', 0, 'CALLDATALOAD')])):
                mapping.append([ -1 , m.offset ])
            
            # If we are adding 4 to a calldataload, it's typically a pointer to somewhere in memory or storage. This is an indicator of an array as calldata
            elif call['opcode'] == "ADD" and (
              (m := _match(call['wrapped'], [(None, 4, 'PUSH1'), (':offset', 0, 'CALLDATALOAD')])) or 
              (m := _match(call['wrapped'], [(':offset', 0, 'CALLDATALOAD'), (None, 4, 'PUSH1')]))
            ):
              mapping.append([ -2 , m.offset ])
            
            # Default to common calldata types
            elif call['opcode'] == "CALLDATALOAD":
              mapping.append([ 256, call['inputs'][0] ])
          
          # the meat of the recursive logic happens here
          if code['opcode']['name'] == "JUMPI":
            if call['inputs']:
              jumpdest = call['inputs'][0]
              
              # if the call is a conditional jump and the condition was true:
              # - create a new VM with the next PC as if this jump wasnt taken
              # - run the current VM with the next PC as if this jump was taken
              #
              # eventually loop detection will reside here. For now, we break out of loops by checking if the next PC was already handled.
              if call['inputs'][1] == 1 and next not in handled:
                handled.append(next)
                mapping += trace(calldata, next, deepcopy(vm.stack), stacktrace=[call], handled=handled)
                
              # the jump conditional wasn't true:
              # - create a new VM with the next PC as if this jump was taken
              # - run the current VM with the next PC as if this jump wasn't taken
              elif jumpdest not in handled:
                handled.append(jumpdest)
                mapping += trace(calldata, jumpdest, deepcopy(vm.stack), stacktrace=[call], handled=handled)
              
              else:
                
                # return with a loop breakout code
                ret = (5, 0)

        # if the current VM execution returned a value:
        if ret:
          
          # save all events from the logs to this function's event list
          for event in vm.logs:
            if event['signature'] not in self.event_signatures:
              self.event_signatures.append(event['signature'])
              self.events.append(event)
          
          # determine the type of the return value
          if ret[0] == 0:
            if self.pure: self.pure = ret[1]
            if self.returns in commonTypes(): self.returns = determineType(self, ret[1])
          
          # the execution REVERTED
          elif ret[0] == 1:
            try:
              revert_string = bytesToType(['string'], ret[1])[0]
              if not '\x00' in revert_string:
                
                # trace backwards through the stacktrace to find the call that caused the revert
                for call in reversed(vm.stacktrace):
                  if call['opcode'] == 'JUMPI' and call['wrapped'][1][0]:
                    
                    # calculate the solidity value of the revert reason
                    revert_reason = solidify_wrapped(call["wrapped"][1], vm, self)
                    
                    # payable detection, pretty crude but working as of ^0.8.14.
                    if 'msg.value == 0' in re.sub(r'[\(\)]*', '', revert_reason):
                      self.payable = False
                    
                    # write the require statements with the revert reasons if applicable, skipping internal requires
                    if any(reason in revert_reason for reason in ['arg', 'var', 'mapping', 'memory',]):
                      if revert_string != "0":
                        self.logic.append([call['pc'], f'require({revert_reason}, "{revert_string}");'])
                      else:
                        self.logic.append([call['pc'], f'require({revert_reason});'])
                    break
                  
            except Exception as e:
              logTraceback(traceback.format_exc(), True)
          
          return mapping
        
        return map(mapping, find_cd_mask)
      return map()

    # convert all calldata accesses to unique values
    accesses = trace(int(self.signature, 16))
    uniques = {}
    for cd in accesses:
      if cd[1] not in uniques:
        uniques[cd[1]] = {
          "val": cd[0] if cd[0] != -2 else None,
          "isPointer": cd[0] == -2
        }
      elif uniques[cd[1]]['val'] in (None, 256):
        uniques[cd[1]] = {
          "val": cd[0] if uniques[cd[1]]['val'] == None else cd[0] if cd[0] != -2 else uniques[cd[1]]['val'],
          "isPointer": uniques[cd[1]]['isPointer'] or cd[0] == -2
        }
    
    # convert unique calldata values to potential solidity types
    potentials = []
    for mask in uniques:
      potentials.append(Logic.resolveMask(uniques[mask]))
    
    # if theres no calldataload and it's a view function but not a pure function, 
    # it's probably a getter function for some public variable
    if len(potentials) == 0 and self.view and not self.pure:
      self.constant = self.storage
    
    # if we are a pure function, calculate the return type
    if self.pure and self.pure != True:
      
        retval = str(bytesToType([self.returns], self.pure)[0])
        if self.returns == 'address':
          retval = Web3.toChecksumAddress(retval.lower())
        elif self.returns == 'string':
          retval = f'\'{retval}\''
          
        self.logic.append([0xFFFFFFFFFFFF, f'return {retval};'])
    
    # handle the returns of some other functions. Needs improvement
    elif self.returns == 'bool':
      self.logic.append([0xFFFFFFFFFFFF, f'return true;'])
    
    # handle matching resolved 4byte functions to potential names
    matches = []
    if self.potentialNames:
      for name in self.potentialNames:
        match = True
        try:
          
          # matching all parameter types with potential types found by CALLDATALOAD processing
          resolvedParameters = re.search(r'\((.*)\)', name).group(1).split(",")
          if "" in resolvedParameters:
            resolvedParameters.remove('')
          if len(potentials) == len(resolvedParameters):
            for i, param in enumerate(resolvedParameters):
              match_any = False
              for j, potential in enumerate(potentials):
                if re.sub(r'(\(|\))*', '', param) in potential:
                  match_any = True
                  potential.pop(j)                  
                  break
              if not match_any:
                match = False
                break
          else:
            match = False
                
        except Exception as e:
          
          # no match if the lengths dont match
          if (len(resolvedParameters) != len(potentials)) and (resolvedParameters[0] != ''):
            match = False
        
        # add match to a list of potential matches  
        if match:
          matches.append(name)
          
    # ask the user to pick a potential function name if there are multiple matches
    if len(matches) > 1:
      logString = 'Multiple function possibilities found:'
      for i, match in enumerate(matches):
        logString += f'\n{" "*25}{"├" if i+1 < len(matches) else "└"}─({colorLib.CYAN}{i}{colorLib.RESET}) {colorLib.CYAN}{match}{colorLib.RESET}'
      
      # if the user has default specified, use the oldest potential name. These tend to be more accurate
      if not self.args.default:
        logString += f'\n\n{" "*25}Select one of the above matches for this function [{len(matches)-1}]: '
        selectionRaw = query('info', str(len(matches)-1), logString)
        if selectionRaw.isnumeric():
          selection = int(selectionRaw)
          if selection > len(matches)-1:
            selection = len(matches)-1
        else:
          selection = len(matches)-1
      else:
        selection = len(matches)-1
        logString += f'\n\n{" "*25}Select one of the above matches for this function [{len(matches)-1}]: {len(matches)-1}'
        log('info', logString)
      self.name = matches[selection]
      
    elif len(matches) > 0:
      self.name = matches[0]

    # build the function's selected calldata types
    ret = []
    if self.name:
      try:
        ret = re.search(r'\((.{1,})\)', self.name).group(1).split(",")
      except: pass
    else: 
      for param in potentials:
        if len(param) > 0:
          ret.append(param[0])
    
    # if theres a resolved name, use it over the placeholder name ( ex: func_ffffffff )
    if self.name:
      self.name = self.name.split("(")[0]
    else:
      self.name = f'func_{self.signature}'

    return tuple(ret)

  # python3 heimdall.py -m 1 -v --default -t 0x4Ae258F6616Fc972aF90b60bFfc598c140C79def
  
  # TODO: re-add internal funcition calls from self.indices