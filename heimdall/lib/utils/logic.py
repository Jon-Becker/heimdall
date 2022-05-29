class Any:
  pass

class Match:
  pass

import math
import re
import traceback
import numexpr

from time import time
from bidict import bidict
from eth_abi import decode_abi
from Crypto.Hash import keccak
from heimdall.lib.utils.logger import logTraceback
sha3 = lambda x: keccak.new(digest_bits=256, data=x).digest()

from .eth.opdict import opcodeDict, opArgNs

class Logic:
  def __init__(self):
    # set constants
    self.UINT256_MAX = 2 ** 256 - 1
    self.UINT255_MAX = 2 ** 255 - 1
    self.UINT256_CEILING = 2 ** 256
    self.UINT255_CEILING = 2 ** 255

  # safely sign an unsigned int
  def sign(self, unsigned):
    if ( unsigned & (1 << (255))) != 0:
      unsigned = unsigned - (1 << 256)
    return unsigned
  
  # safe add
  def add(self, a, b):
    return ((a + b) & self.UINT256_MAX)

  # safe multiplication
  def mul(self, a, b):
    if a == 0 or b == 0:
      return 0
    return ((a * b) & self.UINT256_MAX)

  # safe subtraction
  def sub(self, a, b):
    if a == b:
      return 0
    return ((b - a) & self.UINT256_MAX)

  # safe division
  def div(self, a, b):
    if a == 0 or b == 0:
      return 0
    return ((b // a) & self.UINT256_MAX)

  # safe signed division
  def sdiv(self, a, b):
    if a == 0 or b == 0:
      return 0
    a = self.sign(a)
    b = self.sign(b)
    flip = -1 if a * b < 0 else 1
    return flip * (abs(b) // abs(a))

  # safe modulo
  def mod(self, a, b):
    if a == 0:
      return 0
    return (b % a)

  # safe signed modulo
  def smod(self, a, b):
    a = self.sign(a)
    b = self.sign(b)
    flip = -1 if a < 0 else 1
    if a == 0:
      return 0
    return ( flip * (abs(b) % abs(a))) & self.UINT256_MAX

  # safe addmod operation
  def addmod(self, a, b, c):
    if a == 0:
      return 0
    return ( b + c ) % a

  # safe mulmod operation
  def mulmod(self, a, b, c):
    if a == 0:
      return 0
    return ( b * c ) % a

  # safe exponentiation op
  def exp(self, a, b):
    if a == 0:
      return 1
    if b == 0:
      return 0
    return pow(b, a, self.UINT256_CEILING)

  # pad a hex with null bytes to the given length
  def padHex(self, given_int, given_len):
      hex_result = hex(given_int)[2:]
      num_hex_chars = len(hex_result)
      extra_zeros = '0' * (given_len - num_hex_chars)

      return ('0x' + hex_result if num_hex_chars == given_len else
              '?' * given_len if num_hex_chars > given_len else
              '0x' + extra_zeros + hex_result if num_hex_chars < given_len else
              None)
  
  # calculate the least significant bit of a number
  def leastSignificantByte(self, value):
    if ( len(hex(value)) % 2 == 0 ) and ( value > 0 ):
      hexval = hex(value)
      return int(hexval[-2:],16)
    return 0

  # calculate the byte size of a value
  def byteSize(self, value):
    try:
      return math.ceil(len(hex(value)[2:])/2)
    except:
      return 0
  
  # convert a mask argument into a solidity type
  def resolveMask(args):
    arg = abs(args['val'])
    isPointer = args['isPointer']
    masks = bidict({
        ("bool", "bytes", "uint", "int", 'uint256', 'int256'): -1,
        ("uint8", "int8",): 8,
        ("uint16", "int16",): 16,
        ("uint32", "int32",): 32,
        ("uint64", "int64",): 64,
        ("uint128", "int128",): 128,
        ("address",): 160,
        ("uint256", "int256", "int", "uint", "address"): 256,
    })
    ret = []
    if arg in masks.inverse:
      ret += list(masks.inverse[arg])
    else:
      ret += ['address', 'uint256', 'int256', 'uint', 'int',]
    if arg % 2 == 0:
      bytesize = math.floor( ((arg/8)) )
      ret += [f"bytes{bytesize}", f"bytes{32-bytesize}", f"bytes"]
    
    # if this is used as a pointer, it could be an array
    if isPointer:
      ret += [ f"{potential}[]" for potential in ret]
    return ret

# convert a wrapepd stack value into a solidity logic line
def solidify_wrapped(_wrapped, vm, func=None):
  _ret = 'true'
  try:
    args = []

    # unwrap the value recursively
    def unwrap(_arg, args):
      if _match(_arg, (None, int, str)) or _match(_arg, (int, int, str)) or _match(_arg, (str, int, str)):
        if "PUSH" in _arg[2]:
          args.append(_arg[1])
        elif "CALLDATALOAD" in _arg[2]:
          args.append(f"arg{math.floor((_arg[0] - 4)/32)}")
        else:
          args.append(_arg[2])
      else:
        for arg in _arg:
          if type(arg) == tuple:
            unwrap(arg, args)
          elif type(arg) == str:
            args.append(arg)
    unwrap(_wrapped, args)
    
    # convert the unwrapped values into a solidity line
    _ret = solidity_operation(args, vm, func)
    
  except Exception as e:
    logTraceback(traceback.format_exc(), True)

  return _ret
    
# converts a list of unwrapped stack values into solidity by iterating over them to determine their solidity counterpart
def solidity_operation(_op, vm, func):
  operations = list(reversed(_op))
  while any(isinstance(op, (str,)) and op.lower() in opcodeDict.inverse for op in operations):
    for i, operation in enumerate(operations):
      if isinstance(operation, (str,)) and operation.lower() in opcodeDict.inverse:
        operations.pop(i)
        opInteger = opcodeDict.inverse[operation.lower()]
        opArgN = opArgNs[opInteger]
        opArgs = list(reversed([operations.pop(i-opArgN) for j in range(opArgN)]))
        [solidified, mem, mappings] = solidify(operation, vm, func, *opArgs)
        operations.insert(i-opArgN, solidified)
        break
  return operations[0]


def solidify(opcode, vm, func, *_args, mem={}, mappings={}):
  args = list(_args) + [None for x in range(7)]
    
  # if we run a keccak, save the value to a memory location for later use in mapping calculation
  if opcode == "SHA3":
    _rets = []
    mem['raw'] = sha3(vm.memory.read(0, 64)).hex()
    for n in range(math.floor(int(re.sub(r'[^0-9]', '', str(args[1]))) / 32)):
      _rets.append(offsetToMemoryName(n*32))
      mem[n] = {
        "value": vm.memory.read(n*32, 32).hex(),
        "source": _rets
      }
    return (f'keccak256(abi.encodePacked({" + ".join(_rets)}))', mem, mappings)
  
  # if we are loading from memory, we need to convert the offset into a memory name
  if opcode == "MLOAD":
    return (offsetToMemoryName(args[0]), mem, mappings)
  
  # if we are loading from storage and theres a keccak in the unwrapped stack, its most likely a mapping
  if opcode == "SLOAD" and any("keccak256" in str(arg) for arg in args):
    mappingSlot = int(mem[1]['value'], 16) if 1 in mem else 0
    if mappingSlot <= 32:
      
      # add mapping to the function mapping dict
      if mappingSlot not in func.mappings:
        func.mappings[mappingSlot] = {
          'slot': mappingSlot,
          'key': 'uint256',
          'returns': 'uint256',
        }
        
      if not isinstance(func.memory["var00"]["value"], (str)) and hex(func.memory["var00"]["value"]).startswith("0x4e487b71"):
        if isinstance(func.memlast["var00"]["value"], (str)):
          return (f'mapping_{mappingSlot}[{func.memlast["var00"]["value"]}]', mem, mappings)
        return (f'mapping_{mappingSlot}[EVM_PANIC]', mem, mappings)
      return (f'mapping_{mappingSlot}[{func.memory["var00"]["value"]}]', mem, mappings)
    elif m := resolveSlot(hex(mappingSlot)[2:]):
      
      # add mapping to the function mapping dict
      if m not in func.mappings:
        func.mappings[m] = {
          'slot': m,
          'key': 'uint256',
          'returns': 'uint256',
        }
        
      return (f'mapping_{m}[{func.memlast["var00"]["value"]}][{func.memory["var00"]["value"]}]', mem, mappings)
    else:
      return (f'mapping_generic[{func.memlast["var00"]["value"]}][{func.memory["var00"]["value"]}]', mem, mappings)

  # if the arg contains only arithmetic operations, evaluate them safely
  for i, arg in enumerate(args):
    if isArithmatic(str(arg)):
      try:
        args[i] = numexpr.evaluate(str(arg)).item()
      except: 
        args[i] = (2 ** 256 - 1)
  
  # handle variable casting to solidity type
  if opcode == 'AND':
    mask = False
    
    if isinstance(args[0], (int,)) or args[0].isnumeric():
      mask = int(args[0])
      temp = args[1]
    elif isinstance(args[1], (int,)) or args[1].isnumeric():
      mask = int(args[1])
      temp = args[0]
      
    if mask:
      # mask can either be the 0xFFFFFF kind or bitlength kind
      if re.match('(0x)?[fF]*', hex(mask)):
        castingType = Logic.resolveMask({"val": (len(hex(mask)[2:])*4), "isPointer": False})[0]
      else:
        castingType = Logic.resolveMask({"val": mask, "isPointer": False})[0]
      
      # make sure the variable isnt already cast to the type we are casting to
      isAlreadyCast = (re.match(r'^(int(\d+)?|uint(\d+)?|address|bytes(\d+)?|string|bool)\(.*?\)$', str(temp))) and (temp.split('(')[0] == castingType)
      
      if not isAlreadyCast: 
        return (f'{castingType}({temp})', mem, mappings)
      return (temp, mem, mappings)
  
  # constant solidity values for other opcodes
  solidified = {
    'ADD': f'{args[0]} + {args[1]}',
    'MUL': f'{args[0]} * {args[1]}',
    'SUB': f'{args[0]} - {args[1]}',
    'DIV': f'{args[0]} / {args[1]}',
    'SDIV': f'{args[0]} / {args[1]}',
    'MOD': f'{args[0]} % {args[1]}',
    'SMOD': f'{args[0]} % {args[1]}',
    'ADDMOD': f'({args[0]} + {args[1]}) % {args[2]}',
    'MULMOD': f'({args[0]} * {args[1]}) % {args[2]}',
    'EXP': f'{args[0]} ** {args[1]}',
    'SIGNEXTEND': f'SIGNEXTEND({args[0]}, {args[1]})',
    'LT': f'({args[0]}) < ({args[1]})',
    'GT': f'({args[0]}) > ({args[1]})',
    'SLT': f'({args[0]}) < ({args[1]})',
    'SGT': f'({args[0]}) > ({args[1]})',
    'EQ': f'({args[0]}) == ({args[1]})',
    'ISZERO': f'({args[0]}) == 0',
    'AND': f'{args[0]} & {args[1]}',
    'OR': f'{args[0]} | {args[1]}',
    'XOR': f'{args[0]} ^ {args[1]}',
    'NOT': f'~({args[0]})',
    'BYTE': f'({args[0]} >> (248 - {args[1]} * 8)) && 0xFF',
    'SHL': f'{args[0]} << {args[1]}',
    'SHR': f'({args[0]}) >> ({args[1]})',
    'SAR': f'{args[0]} >> {args[1]}',
    'SHA3': f'keccak256({args[0]})',
    'LOG0': f'emit {args[0]}()',
    'LOG1': f'emit {args[0]}({args[1]})',
    'LOG2': f'emit {args[0]}({args[1]}, {args[2]})',
    'LOG3': f'emit {args[0]}({args[1]}, {args[2]}, {args[3]})',
    'LOG4': f'emit {args[0]}({args[1]}, {args[2]}, {args[3]}, {args[4]})',
    'CREATE': f'// Contract appears to CREATE a new contract',
    'CREATE': f'// Contract appears to CREATE2 a new contract',
    'ADDRESS': 'address(this)',
    'BALANCE': f'address({args[0] if args[0] != None else "this"}).balance',
    'ORIGIN': 'tx.origin',
    'CALLER': 'msg.sender',
    'CALLVALUE': 'msg.value',
    'CALLDATASIZE': 'msg.data.length',
    'GASPRICE': 'tx.gasprice',
    'BLOCKHASH': f'blockhash({args[0] if args[0] != None else "block.number"})',
    'COINBASE': 'block.coinbase',
    'TIMESTAMP': 'block.timestamp',
    'NUMBER': 'block.number',
    'DIFFICULTY': 'block.difficulty',
    'GASLIMIT': 'block.gaslimit',
    'CHAINID': 'block.chainid',
    'SELFBALANCE': 'address(this).balance',
    'GAS': 'gasleft()',
    'SLOAD': f'LOAD{{{args[0]}}}',
    'RETURNDATASIZE': f'ext0.length'
  }
  
  try:
    return (solidified[opcode.upper()], mem, mappings)
  except Exception as e:
    return (opcode, mem, mappings)
  
# resolves a slot to a mapping
def resolveSlot(hex):
  for i in range(0, 0x20):
    if sha3(bytearray.fromhex(str(i).rjust(128, "0"))).hex() == hex:
      return i
  return False

# checks if a any list is in a list
def listContainsList(needleList, haystack):
  for needle in needleList:
    if needle in haystack:
      return True
  return False

# a recursive match function which can match dynamic expressions to patterns
def _match(expression, pattern):
  def _matcher(exp, pat, m):
    if isinstance(pat, str) and ":" in pat:
      setattr(m, pat.replace(":", ""), exp)
      return

    if pat is Any:
      return

    if isinstance(pat, (list, tuple)):
      if not isinstance(exp, (list, tuple)):
        raise ValueError()

      while True:
        if len(pat) == 0 and len(exp) == 0:
          return

        if pat[0] is Any:
          return

        _matcher(exp[0], pat[0], m)
        exp = exp[1:]
        pat = pat[1:]
    
    if isinstance(pat, type):
      if isinstance(exp, pat):
        return
      raise ValueError()
    
    if exp != pat:
      raise ValueError()
      

  try:
    match = Match()
    _matcher(expression, pattern, match)
  except Exception as e:
    return False
  return match

# determines the type of the given bytes, using length and decoding as heuristics
def determineType(func, retbytes):
  determined = "bytes"
  try:
    if type(retbytes) == int:
      retbytes = hex(retbytes)
    return_value = retbytes[2:]
    return_words = [return_value[index : index + 64] for index in range(0, len(return_value), 64)]
    
    # if theres more than one word, its an array or bytes or string
    if len(return_words) > 1:
      determined = "string"
    else:
      
      # its a single type, uint256, address, bool, or bytes32
      if retbytes == '0x0000000000000000000000000000000000000000000000000000000000000000':
        if func != None:
          func.warnings.append(f'/// @custom:warning This function returns either a boolean, uint, bytes32, or address.')
          func.warnings.append(f'///                   It\'s impossible to determine the exact return type.')
        determined = 'uint256'
      elif retbytes == '0x0000000000000000000000000000000000000000000000000000000000000001':
        if func != None:
          func.warnings.append(f'/// @custom:warning This function returns either a boolean, uint, bytes32, or address.')
          func.warnings.append(f'///                   It\'s impossible to determine the exact return type.')
        determined = 'bool'
      elif 20 <= len(retbytes[2:].replace("0", "", 64)) <= 40 :
        determined = 'address'
      else:
        if func != None:
          func.warnings.append(f'/// @custom:warning This function returns either a boolean, uint, bytes32, or address.')
          func.warnings.append(f'///                   It\'s impossible to determine the exact return type.')
        determined = 'uint256'
      
  except Exception as e:
    pass

  return determined

# some common types that we should override if possible
def commonTypes():
  return ('bytes', 'bytes[]', None)

# converting bytes to a given type, usually used for converting bytes to a string like revert reasons
def bytesToType(type, retbytes):
  try:
    return decode_abi(type, bytes.fromhex(retbytes[2:].replace('08c379a0', '')))
  except:
    return retbytes

# calculates a variable name from the offset provided
def offsetToMemoryName(offset): 
  try:
    return f'var{hex(math.floor(offset/4))[2:].ljust(2, "0")}'
  except:
    return offset
  
# ensures that s includes only the allowed characters for expressions.
def isArithmatic(s):  
  allowed_charset = "0123456789-+/*()%^<>!&|~. "
  return all(ch in allowed_charset for ch in s)