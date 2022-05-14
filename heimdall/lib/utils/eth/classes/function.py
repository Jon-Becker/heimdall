from copy import deepcopy
import re
from web3 import Web3

from ...logic import Any, Logic, _match, bytesToType, commonTypes, determineType, solidify_wrapped, offsetToMemoryName, solidify
from ...apis.sigdir import resolve
from ...eth.classes.vm import VirtualMachine
from ...eth.classes.stack import Stack
from ...logger import log, query, progress_bar
from ...colors import colorLib

class Function():
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
      
  def isFunctionCall(self, dest):
    return dest in [item for sublist in self.indices.keys() for item in sublist]

  def getEntryPoint(self):
    vm = deepcopy(VirtualMachine(_assembly=self.assembly, _calldata=int(self.signature, 16)))
    def resolve(entries=[], logJump=False):
      try:
        instructionIndex = list(self.assembly.keys()).index(vm.instruction)
        code = self.assembly[vm.instruction]
        lastPC = vm.instruction
        vm.lastInstruction = lastPC
        vm.instruction = (list(self.assembly.keys())[instructionIndex+1])
        if vm.instruction > self.endDispatcher:
          return tuple(entries)
        
        vm.execute(code['opcode']['name'], code['argument'])
        call = vm.stacktrace[-1]
                
        if call['opcode'] == "PUSH4" and call['outputs'] == int(self.signature, 16):
          return resolve(entries, True)
              
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
        if self.args.verbose:
          log('warning', 'Exception encountered when resolving function index.')
    return resolve()
  def resolveParams(self):
    def trace(calldata, startPoint=1, stack=Stack(), stacktrace=[], handled=[]):
      vm = deepcopy(VirtualMachine(_assembly=self.assembly, _calldata=calldata, _instruction=startPoint, _stack=stack, _stacktrace=stacktrace))
      
      def map(mapping=[], getMask=False):
        find_cd_mask = getMask
        instructionIndex = list(self.assembly.keys()).index(vm.instruction)
        code = self.assembly[vm.instruction]
        lastPC = vm.instruction
        vm.lastInstruction = lastPC
        vm.instruction = (list(self.assembly.keys())[instructionIndex+1])
        next = (list(self.assembly.keys())[instructionIndex+1])
        
        ret = vm.execute(code['opcode']['name'], code['argument'])
        call = vm.stacktrace[-1]
        
        if call['pc'] > self.endDispatcher:
          if call['opcode'] in ['SSTORE', 'SLOAD', 'DELEGATECALL', 'STATICCALL', 'CALL', 'CALLCODE']:
            self.pure = False
            if call['opcode'] == "SLOAD":
              self.storage = solidify_wrapped(call["wrapped"], vm, self)
                          
            elif call['opcode'] == "SSTORE":
              key = solidify_wrapped(("SLOAD", Any, call['wrapped'][0]), vm, self)
              value = solidify_wrapped(call["wrapped"][1:], vm, self)
              
              if "_mapping_" in key:
                if key.split("[")[0] not in self.mappings:
                  self.mappings[key.split("[")[0]] = {
                    'slot': key.split("[")[0],
                    'key': 'uint256',
                    'returns': 'uint256',
                  }
              self.logic.append([call['pc'], f'{key} = {value};'])
              self.view = False

            else:
              callParameters = call['inputs']
              if call['opcode'] in ['CALL', 'CALLCODE']:
                callParameters.pop(2)
              
              print(callParameters)
              self.logic.append([call['pc'] ,f'(bool success, bytes{callParameters[-1]} memory ext0) = address({Web3.toChecksumAddress(Logic.padHex(None, callParameters[1], 40))}).staticcall();'])
              
              self.view = False

          if call['opcode'] in ['DELEGATECALL', 'STATICCALL', 'CALL', ]:
            self.external = True

          if call['opcode'] in ['MSTORE', 'MSTORE8']:
            try:
              self.memlast[offsetToMemoryName(call["inputs"][0])] = self.memory[offsetToMemoryName(call["inputs"][0])]
            except:
              pass
            self.memory[offsetToMemoryName(call["inputs"][0])] = {
              "value": solidify_wrapped(call["wrapped"][1:], vm, self),
              "pc": call['pc']
            }

          if 'LOG' in call['opcode']:
            sources = []
            for temp in call['wrapped']:
              sources.append(str(solidify_wrapped(temp, vm, self)))
            sources += call['event']['topics']['unindexed']
            [self.logic.append([call['pc'], f'bytes memory {source} = {self.memory[source]["value"]};']) for source in sources if re.match(r"var[0-9]*", source)]
            self.logic.append([call['pc'], f'emit Event_{call["event"]["signature"][:10]}({", ".join(sources)});'])
            pass

          if 'wrapped' in call and call['wrapped'] != None:
            if call['opcode'] == "AND" and (
              (m := _match(call['wrapped'], [(':offset', 0, 'CALLDATALOAD'), (None, ':mask', Any)])) or 
              (m := _match(call['wrapped'], [(None, ':mask', Any), (':offset', 0, 'CALLDATALOAD')]))
            ):
              mapping.append([ (len(hex(m.mask)[2:])*4) , m.offset ])
                
            elif call['opcode'] == 'ISZERO':
              if(m := _match(call['wrapped'], [(':offset', 0, 'CALLDATALOAD')])):
                mapping.append([ -1 , m.offset ])
                
            elif call['opcode'] == "ADD" and (
              (m := _match(call['wrapped'], [(None, 4, 'PUSH1'), (':offset', 0, 'CALLDATALOAD')])) or 
              (m := _match(call['wrapped'], [(':offset', 0, 'CALLDATALOAD'), (None, 4, 'PUSH1')]))
            ):
              pass
              mapping.append([ -2 , m.offset ])
              
            elif call['opcode'] == "CALLDATALOAD":
              mapping.append([ 256, call['inputs'][0] ])
              
          if code['opcode']['name'] == "JUMPI":
            if call['inputs']:
              jumpdest = call['inputs'][0]                
              if call['inputs'][1] == 1 and next not in handled:
                handled.append(next)
                mapping += trace(calldata, next, deepcopy(vm.stack), stacktrace=[call], handled=handled)
              elif jumpdest not in handled:
                handled.append(jumpdest)
                mapping += trace(calldata, jumpdest, deepcopy(vm.stack), stacktrace=[call], handled=handled)
              else:
                ret = (5, 0)

        if ret:
          # no need here
          for event in vm.logs:
            if event['signature'] not in self.event_signatures:
              self.event_signatures.append(event['signature'])
              self.events.append(event)
          
          if ret[0] == 0:
            if self.pure:
              self.pure = ret[1]
            
            if self.returns in commonTypes():
              self.returns = determineType(self, ret[1])
                          
          elif ret[0] == 1:
            try:
              revert_string = bytesToType(['string'], ret[1])[0]
              if not '\x00' in revert_string:
                
                for call in reversed(vm.stacktrace):
                  if call['opcode'] == 'JUMPI' and call['wrapped'][1][0] :
                    
                    self.logic.append([call['pc'], f'require({solidify_wrapped(call["wrapped"][1], vm, self)}, "{revert_string}");'])
                    
                    break
            except Exception as e:
              pass
          
          return mapping
        
        return map(mapping, find_cd_mask)
      return map()

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
    potentials = []
    for mask in uniques:
      potentials.append(Logic.resolveMask(uniques[mask]))
    
    if len(potentials) == 0 and self.view and not self.pure:
      self.constant = self.storage
    
    if self.pure and self.pure != True:
        retval = str(bytesToType([self.returns], self.pure)[0])

        if self.returns == 'address':
          retval = Web3.toChecksumAddress(retval.lower())

        if self.returns == 'string':
          retval = f'\'{retval}\''
          
        self.logic.append([0xFFFFFFFFFFFF, f'return {retval};'])
    elif self.returns == 'bool':
      self.logic.append([0xFFFFFFFFFFFF, f'return true;'])
    
    matches = []
    if self.potentialNames:
      for name in self.potentialNames:
        match = True
        try:
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
          if (len(resolvedParameters) != len(potentials)) and (resolvedParameters[0] != ''):
            match = False
            
        if match:
          matches.append(name)
    if len(matches) > 1:
      logString = 'Multiple function possibilities found:'
      for i, match in enumerate(matches):
        logString += f'\n{" "*25}{"├" if i+1 < len(matches) else "└"}─({colorLib.CYAN}{i}{colorLib.RESET}) {colorLib.CYAN}{match}{colorLib.RESET}'
        
      if not self.args.default:
        logString += f'\n\n{" "*25}Select one of the above matches for this function [0]: '
        selectionRaw = query('info', "0", logString)
        if selectionRaw.isnumeric():
          selection = int(selectionRaw)
          if selection > len(matches)-1:
            selection = 0
        else:
          selection = 0
      else:
        selection = 0
        logString += f'\n\n{" "*25}Select one of the above matches for this function [0]: 0'
        log('info', logString)
      self.name = matches[selection]
    elif len(matches) > 0:
      self.name = matches[0]

    ret = []
    if self.name:
      try:
        ret = re.search(r'\((.{1,999999999})\)', self.name).group(1).split(",")
      except: pass
    else: 
      for param in potentials:
        if len(param) > 0:
          ret.append(param[0])
    
    if self.name:
      self.name = self.name.split("(")[0]
    else:
      self.name = f'func_{self.signature}'

    return tuple(ret)
  
  # TODO: payable detection
  # eseentially if ISZERO CALLVALUE -> JUMPI 1 -> REVERT
  #   > payable
  # if ISZERO CALLVALUE -> JUMPI 0 -> REVERT
  #   > nonpayable
  # merely looking for callvalue opcode isn't enough.
  # 

  # python3 heimdall.py -m 1 -v --default -t 0x4Ae258F6616Fc972aF90b60bFfc598c140C79def
  
  # TODO: re-add internal funcition calls from self.indices