from inspect import signature
import os
import sys

from numpy import sign

from bidict import bidict

from ..logger import log, progress_bar
from ..version import getLocalVersion
from ..colors import colorLib
from ..postprocess import postProcess
from ..version import getLatestSolidityRelease
from ..io import appendLine, write
from ..eth.functions import resolveFunctions

def build(assembly, args, output, web3, onlyAbi=False):
  sys.setrecursionlimit(5000)
  # abi = loadFileAsJson(f'{output}/abi.json')
  # indices = bidict(loadFileAsPickle(f'{output}/__cache__/indices.hc'))
  # signatures = loadFileAsPickle(f'{output}/__cache__/signatures.hc')

  [abi, functions, indices, signatures, events, constantStorage, mappings] = resolveFunctions(assembly, args, output)
  
  if not onlyAbi:
    sourcefile = f'{output}/decompiled.sol'
    indent_level = 0
    
    if args.verbose:
      log('info', f'Creating source file {colorLib.CYAN}{sourcefile.replace(os.getcwd(), ".")}{colorLib.RESET}')
    
    source_header = f'''// SPDX-License-Identifier: MIT
pragma solidity {getLatestSolidityRelease()};

/// @title            Heimdall decompiled contract
/// @author           Jonathan Becker <jonathan@jbecker.dev>
/// @custom:version   {getLocalVersion()}
///
/// @notice           This contract was created using Heimdall toolkit's decompiler.
///                     It was generated directly by tracing the EVM opcodes from this contract.
///                     As a result, it may not compile or even be valid solidity code.
///                     Despite this, it should be obvious what each function does. Overall
///                     logic should have been preserved throughout decompiling.
///
/// @dev              Sometimes, return types don't match up with their originals. This
///                     shouldn't affect anything, but you should keep it in mind. The
///                     documentation goes into better detail on this.
/// @custom:github    You can find the open-source decompiler here
///                       https://github.com/Jon-Becker/heimdall
/// @custom:donations I spent ~250 hours on this program. It's open source and will always be
///                     free to use, so donations are always appreciated if you find it helpful.
///                     0x6666666b0B46056247E7D6cbdb78287F4D12574d   OR   jbecker.eth
'''

    write(sourcefile, source_header)
    lines = [
      f'contract Heim_{args.target[2:16]} {{',
      f'}}'
    ]

    def addline(line="", n=1, natspec=False):
      line = postProcess(line, signatures, events, constantStorage)
      
      for i in range(n):
        if natspec:
          lines.insert(-1, line)
        else:
          lines.insert(-1, line.replace("  ", " "))
    
    if any(interface['type'] == "event" for interface in abi):
      addline('''/// @notice         Contract event declaration
  /// @dev            If the signature wasn't resolved, parsing it is near-impossible. For now,
  ///                   we will default to bytes. TODO: indexed
  ''', natspec=True)
      for event in [interface for interface in abi if interface['type'] == 'event']:
        inputs = []
        for input in event['inputs']:
          inputs.append(f'{input["type"]} {input["name"]}')
        inputs = str(tuple(inputs)).replace("'", "").replace(",)", ")")
        
        addline(f'event {event["name"]}{inputs};')
      addline(n=2)
    
    addline('''/// @notice           Heimdall constant declarations
  /// @dev              The below variables are used by Heimdall to mark panics, crashes,
  ///                     and other decompiler issues. These aren't present in the original
  ///                     contract, and are purely used for heuristics.
  
  string private constant EVM_PANIC = "Heimdall EVM panic! Report this with a GitHub issue.";
  
  /// @dev              Mappings that are dynamic but unresolved will be marked as generic.
  ///                     Please keep in mind multiple mappings may be marked as this generic
  ///                     mapping but still be separate mappings.
  
  mapping(bytes => mapping(bytes => bytes)) public _mapping_generic;
  ''', natspec=True)
    
    if any('constant' in interface and interface['constant'] == True for interface in abi):
      addline('''/// @notice           Contract variable declaration
  /// @dev              These variables have been detected because their getters
  ///                     were detected. These may or may not be in the constructor.
  ///                     Mappings will also appear here, if resolved.
  ''', natspec=True)
      
      if len(mappings) > 0:
        for mapping in mappings:
          addline(f'mapping({mapping["key"]} => {mapping["returns"]}) public {mapping["slot"]};')
        addline(n=1)
      
      for constant in [interface for interface in abi if 'constant' in interface and interface['constant']]:
        outputs = []
        if "outputs" in constant:
          for output in constant['outputs']:
            outputs.append(f'{output["type"]} private ')
        if len(outputs) > 0:
          addline(f'{outputs[0]} _{constant["name"]};')
        else:
          addline(f'bytes private _{constant["name"]};')
      addline(n=2)
      
    if any(interface['type'] == "constructor" for interface in abi):
      addline(f'constructor()  {{}}')
      addline(n=2)
      
    if any(interface['type'] == "function" for interface in abi):
      addline('''/// @notice         Contract function declaration
  /// @dev            Below is the function logic. As stated in the header, these will
  ///                   be *outlines* of the function logic and won't be exact.
  ///                   There are plans to improve this in the future.
  /// @notice         Additionally, view, pure, and payable detection are a bit buggy as of
  ///                   v1.0.0. There are plans to improve this detection.
  ''', natspec=True)
      for getter in [interface for interface in abi if interface['type'] == 'function' and 'constant' in interface and interface['constant']]:
        outputs = []
        if "outputs" in getter:
          for output in getter['outputs']:
            outputs.append(f'{output["type"]} {"memory" if (output["type"] in ["string", "bytes"] or "[]" in output["type"]) else ""} {output["name"]}')
          output = str(tuple(outputs)).replace("'", "").replace(",)", ")")
        
        addline()
        if len(outputs) <= 0:
           addline('''/// @custom:warning No output found, reverting to bytes for this getter.''', natspec=True)
        addline(f'function {getter["name"]}() public '
                  f'{getter["stateMutability"] if getter["stateMutability"] != "nonpayable" else ""}'
                  f'{f" returns {output}" if len(outputs) > 0 else " returns (bytes memory ret0)"}'
                  f' {{')
        
        for func in functions:
          if func.name == getter['name']:
            logic = sorted(func.logic, key=lambda x: x[0])
            for line in [x[1] for x in logic]:
              addline(line)
            break
        
        addline(f'return _{getter["name"]};')
        
        addline(f'}}')
      addline(n=2)
      for interface in [interface for interface in abi if interface['type'] == 'function' and 'constant' in interface and not interface['constant']]:
        inputs = []
        for input in interface['inputs']:
          inputs.append(f'{input["type"]} {"calldata" if (input["type"] in ["string", "bytes"] or "[]" in input["type"]) else ""} {input["name"]}')
        inputs = str(tuple(inputs)).replace("'", "").replace(",)", ")")
        outputs = []
        if "outputs" in interface:
          for output in interface['outputs']:
            outputs.append(f'{output["type"]} {"memory" if (output["type"] in ["string", "bytes"] or "[]" in output["type"]) else ""} {output["name"]}')
          output = str(tuple(outputs)).replace("'", "").replace(",)", ")")
        
        addline()
        for func in functions:
          if func.name == interface['name']:
            for line in func.warnings:
              addline(line, natspec=True)
              
        addline(f'function {interface["name"]}{inputs} public '
                  f'{interface["stateMutability"] if interface["stateMutability"] != "nonpayable" else ""}'
                  f'{f" returns {output}" if len(outputs) > 0 else ""}'
                  f' {{')
        
        for func in functions:
          if func.name == interface['name']:
            logic = sorted(func.logic, key=lambda x: x[0])
            uniques = []
            for line in logic:
              if line[1] not in uniques:
                uniques.append(line[1])

            for line in uniques:
              addline(line)
              
            break
              
        addline(f'}}')

    for line in progress_bar(lines, args):
      if line.startswith("}"):
        indent_level -= 2
        
      appendLine(sourcefile, f'\n{" "*indent_level}{line}')
      
      if line.endswith("{"):
        indent_level += 2
  
  log('success', f'Contract decompiled! Wrote source to {colorLib.GREEN}{sourcefile.replace(os.getcwd(), ".")}{colorLib.RESET}')
  return {
    "abi": abi
  }