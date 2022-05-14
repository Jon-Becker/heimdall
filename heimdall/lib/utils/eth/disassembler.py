import os
import math
import json

from ..logger import log
from ..colors import colorLib
from ..io import outputDirectory, write
from ..eth.opdict import opcodeDict


def disassemble(bytecode, output, args):
  log('info', f'Beginning bytecode disassembly...')

  assemblyOut = []
  assembly = {}
  
  opIndex = 0

  totalBytes = len(str(math.floor(len(bytecode)/2)))
  hexBytes = len(hex(math.floor(len(bytecode)/2))[2:])

  while opIndex < len(bytecode):
    opint = int(bytecode[opIndex:opIndex+2], 16)
    ophex = hex(opint)
    
    if opint in opcodeDict:
      opcode = opcodeDict[ opint ].upper()
      pushVal = ""
      
      if "PUSH" in opcode:
        byteCount = int(opcode.replace("PUSH", ""))
        pushVal = bytecode[opIndex+2:(opIndex+2) + byteCount * 2 ]
        opIndex += byteCount*2

      assemblyOut.append(f'{hex(math.floor((opIndex)/2))[2:].zfill(hexBytes)} { str(math.floor((opIndex)/2)).zfill(totalBytes) } {opcode} {pushVal}')
      assembly[math.floor((opIndex)/2)] = {
        "instruction": math.floor((opIndex)/2),
        "opcode": {
          "hex": ophex,
          "int": opint,
          "name": opcode
        },
        "argument": int(pushVal, 16) if pushVal else ''
      }
    else:
      assemblyOut.append(f'{hex(math.floor((opIndex)/2))[2:].zfill(hexBytes)} { str(math.floor((opIndex)/2)).zfill(totalBytes) } unknown')
      assembly[math.floor((opIndex)/2)] = {
        "instruction": math.floor((opIndex)/2),
        "opcode": {
          "hex": ophex,
          "int": opint,
          "name": "unknown operation"
        },
        "argument": ""
      }

    opIndex += 2

  log('success', f'Disassembled {colorLib.GREEN}{str(math.floor(len(bytecode)/2))}{colorLib.RESET} bytes successfully.')
  write(f'{output}/assembly.asm', "\n".join(assemblyOut))
  return assembly