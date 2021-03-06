from curses import has_key
import math
import traceback
import rlp
import copy

from web3 import Web3
web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/422705d85b5c4923b841a60ba0c01129"))


from ...logger import log
from ...colors import colorLib
from ...logic import Logic, offsetToMemoryName
from ...eth.classes.stack import Stack
from ...eth.classes.memory import Memory

from Crypto.Hash import keccak
sha3 = lambda x: keccak.new(digest_bits=256, data=x).digest()

class VirtualMachine:
  
  # initialize the virtual machine with a set of options for initial EVM state
  def __init__(self, 
    _stack = Stack(),
    _memory= Memory(), 
    _storage={}, 
    _calldata=0,
    _address=0, 
    _origin=0, 
    _caller=0, 
    _callValue=0, 
    _bytecode=0, 
    _returnData=0,
    _assembly={},
    _instruction=1,
    _gas=1000000,
    _stacktrace=[],
    _logEvents=False):
    self.stack = _stack
    self.memory = _memory
    self.storage = _storage
    self.calldata = _calldata
    self.address = _address
    self.caller = _caller
    self.origin = _origin
    self.value = _callValue
    self.bytecode = _bytecode
    self.returnData = _returnData
    self.assembly = _assembly
    self.gas = _gas
    self.instruction = _instruction
    self.lastInstruction = _instruction
    self.logs = []
    self.stacktrace = _stacktrace
    self.logic = Logic()
    self.logEvents = _logEvents
    
  # convert any hex to a checksummed address
  def toAddress(self, hex):
    return Web3.toChecksumAddress(self.logic.padHex(hex, 40))
  
  # appends an event to the logs
  def logEvent(self, event):
    self.logs.append(event)
    
  # gets the current EVM stack
  def getStack(self):
    return self.stack.getStack()
  
  # gets the current EVM memory
  def getMemory(self):
    return self.memory
  
  # gets the current EVM storage
  def getStorage(self):
    return self.storage
  
  # gets the last operation performed in the EVM
  def lastOperation(self, n=1):
    try:
      return self.stacktrace[ (n*-1) ]
    except:
      return None
    
  # executes an operation on the EVM 
  def execute(self, opcode, args=None):
    try:
      if type(args) != int:
        args=None

      # pushes a value onto the stack
      if 'PUSH' in opcode:
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "inputs": None,
            "outputs": int(args),
          }
        )
        self.stack.append( int(args), source=opcode )

      # stops execution and returns a value from memory
      elif opcode == 'RETURN':
        [offset_wrapped, size_wrapped] = self.stack.pop(2)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [offset_wrapped, size_wrapped],
            "inputs": [offset_wrapped[1], size_wrapped[1]],
            "outputs": None,
          }
        )
        return (0, f'0x{self.memory.read(offset_wrapped[1], size_wrapped[1]).hex()}')

      # stops execution with an error and returns a value from memory
      elif opcode == 'REVERT':
        [offset_wrapped, size_wrapped] = self.stack.pop(2)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [offset_wrapped, size_wrapped],
            "inputs": [offset_wrapped[1], size_wrapped[1]],
            "outputs": None,
          }
        )
        try:
          ret = f'0x{self.memory.read(offset_wrapped[1], size_wrapped[1]).hex()}'
          return (1, ret)
        except:
          return (1, f'0x')
      
      # stops execution with an error
      elif opcode == 'INVALID':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": (0, 0,),
            "inputs": (0,0,),
            "outputs": None,
          }
        )
        try:
          ret = f'0x{self.memory.read(0,0).hex()}'
          return (2, ret)
        except:
          return (2, f'0x')

      # stops execution and destroys the evm instance
      elif opcode == 'SELFDESTRUCT':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": None,
          }
        )
        return (3, f'0x')

      # sums the top two values on the stack
      elif opcode == 'ADD':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.add(a, b),
          }
        )
        self.stack.append(self.logic.add(a, b), op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # multiplies the top two values on the stack
      elif opcode == 'MUL':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.mul(a, b),
          }
        )
        self.stack.append(self.logic.mul(a, b), op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # subtracts the top two values on the stack
      elif opcode == 'SUB':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.sub(a, b),
          }
        )
        self.stack.append(self.logic.sub(a, b), op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # divides the top two values on the stack
      elif opcode == 'DIV':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.div(a, b),
          }
        )
        self.stack.append(self.logic.div(a,b), op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # signed division of the top two values on the stack
      elif opcode == 'SDIV':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.sdiv(a, b),
          }
        )
        self.stack.append(self.logic.sdiv(a,b), op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # calculates the modulo of the top two values on the stack
      elif opcode == 'MOD':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.mod(a, b),
          }
        )
        self.stack.append(self.logic.mod(a,b), op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # calculates the signed modulo of the top two values on the stack
      elif opcode == 'SMOD':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.smod(a, b),
          }
        )
        self.stack.append(self.logic.smod(a,b), op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # calculates the modulo of the third value on the stack with the sum of the top two values on the stack
      elif opcode == 'ADDMOD':
        [c_wrapped, b_wrapped, a_wrapped] = self.stack.pop(3)
        [c, b, a] = self.stack.unwrap([c_wrapped, b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [c_wrapped, b_wrapped, a_wrapped],
            "inputs": [c, b, a],
            "outputs": self.logic.addmod(a, b, c),
          }
        )
        self.stack.append(self.logic.addmod(a,b,c), op=opcode, source=tuple([c_wrapped, b_wrapped, a_wrapped]))

      # calculates the modulo of the third value on the stack with the product of the top two values on the stack
      elif opcode == 'MULMOD':
        [c_wrapped, b_wrapped, a_wrapped] = self.stack.pop(3)
        [c, b, a] = self.stack.unwrap([c_wrapped, b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [c_wrapped, b_wrapped, a_wrapped],
            "inputs": [c, b, a],
            "outputs": self.logic.mulmod(a, b, c),
          }
        )
        self.stack.append(self.logic.mulmod(a,b,c), op=opcode, source=tuple([c_wrapped, b_wrapped, a_wrapped]))

      # calculates the exponential of the top two values on the stack
      elif opcode == 'EXP':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": self.logic.exp(a, b),
          }
        )
        self.stack.append(self.logic.exp(a,b), op=opcode, source=tuple([b_wrapped, a_wrapped]))
      
      #  extends the sign bit of the top value on the stack
      elif opcode == 'SIGNEXTEND':
        [x_wrapped, b_wrapped] = self.stack.pop(2)
        [x, b] = self.stack.unwrap([x_wrapped, b_wrapped])
        if x < 32:
          tbit = x * 8 + 7
          sbit = 1 << tbit
          if b & sbit:
            self.stacktrace.append(
              {
                "pc": self.lastInstruction,
                "opcode": opcode,
                "wrapped": [x_wrapped, b_wrapped],
                "inputs": [x, b],
                "outputs": b | (self.logic.UINT256_CEILING - sbit),
              }
            )
            self.stack.append( b | (self.logic.UINT256_CEILING - sbit), op=opcode, source=tuple([x_wrapped, b_wrapped]) )
          else:
            self.stacktrace.append(
              {
                "pc": self.lastInstruction,
                "opcode": opcode,
                "wrapped": [x_wrapped, b_wrapped],
                "inputs": [x, b],
                "outputs": b & (sbit - 1),
              }
            )
            self.stack.append( b & (sbit - 1), op=opcode, source=tuple([x_wrapped, b_wrapped])  )
        else:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [x_wrapped, b_wrapped],
              "inputs": [x, b],
              "outputs": b,
            }
          )
          self.stack.append( b, op=opcode, source=tuple([x_wrapped, b_wrapped])  )

      # less than comparison
      elif opcode == 'LT':
        [a_wrapped, b_wrapped] = self.stack.pop(2)
        [a, b] = self.stack.unwrap([a_wrapped, b_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [a_wrapped, b_wrapped],
            "inputs": [a, b],
            "outputs": 1 if a < b else 0,
          }
        )
        self.stack.append(1 if a < b else 0, op=opcode, source=tuple([a_wrapped, b_wrapped]))
      
      # greater than comparison
      elif opcode == 'GT':
        [a_wrapped, b_wrapped] = self.stack.pop(2)
        [a, b] = self.stack.unwrap([a_wrapped, b_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [a_wrapped, b_wrapped],
            "inputs": [a, b],
            "outputs": 1 if a > b else 0,
          }
        )
        self.stack.append(1 if a > b else 0, op=opcode, source=tuple([a_wrapped, b_wrapped]))

      # signed less than comparison
      elif opcode == 'SLT':
        [a_wrapped, b_wrapped] = self.stack.pop(2)
        [a, b] = self.stack.unwrap([a_wrapped, b_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [a_wrapped, b_wrapped],
            "inputs": [a, b],
            "outputs": 1 if a < b else 0,
          }
        )
        self.stack.append(1 if a < b else 0, op=opcode, source=tuple([a_wrapped, b_wrapped]))

      # signed greater than comparison
      elif opcode == 'SGT':
        [a_wrapped, b_wrapped] = self.stack.pop(2)
        [a, b] = self.stack.unwrap([a_wrapped, b_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [a_wrapped, b_wrapped],
            "inputs": [a, b],
            "outputs": 1 if a > b else 0,
          }
        )
        self.stack.append(1 if a > b else 0, op=opcode, source=tuple([a_wrapped, b_wrapped]))

      # equality comparison
      elif opcode == 'EQ':
        [a_wrapped, b_wrapped] = self.stack.pop(2)
        [a, b] = self.stack.unwrap([a_wrapped, b_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [a_wrapped, b_wrapped],
            "inputs": [a, b],
            "outputs": 1 if a == b else 0,
          }
        )
        self.stack.append(1 if b == a else 0, op=opcode, source=tuple([a_wrapped, b_wrapped]))

      # not equal comparison
      elif opcode == 'ISZERO':
        [a_wrapped] = self.stack.pop(1)
        [a] = self.stack.unwrap([a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [a_wrapped],
            "inputs": [a],
            "outputs": 1 if a == 0 else 0,
          }
        )
        self.stack.append(1 if a == 0 else 0, op=opcode, source=tuple([a_wrapped]))

      # and operation
      elif opcode == 'AND':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": a & b,
          }
        )
        self.stack.append(a & b, op=opcode, source=tuple([b_wrapped, a_wrapped]))
    
      # or operation
      elif opcode == 'OR':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": a | b,
          }
        )
        self.stack.append(a | b, op=opcode, source=tuple([b_wrapped, a_wrapped]))
    
      # xor operation
      elif opcode == 'XOR':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [b_wrapped, a_wrapped],
            "inputs": [b, a],
            "outputs": a ^ b,
          }
        )
        self.stack.append(a ^ b, op=opcode, source=tuple([b_wrapped, a_wrapped]))

      # not operation
      elif opcode == 'NOT':
        [a_wrapped] = self.stack.pop(1)
        [a] = self.stack.unwrap([a_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [a_wrapped],
            "inputs": [a],
            "outputs": (~a) & self.logic.UINT256_MAX,
          }
        )
        self.stack.append( (~a) & self.logic.UINT256_MAX, op=opcode, source=tuple([a_wrapped]) )

      # calculates the byte value of a word
      elif opcode == 'BYTE':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        if b >= 32:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [b_wrapped, a_wrapped],
              "inputs": [b, a],
              "outputs": 0,
            }
          )
          self.stack.append( 0, op=opcode, source=tuple([b_wrapped, a_wrapped])  )
        else:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [b_wrapped, a_wrapped],
              "inputs": [b, a],
              "outputs": (a // pow(256, 31 - b)) % 256,
            }
          )
          self.stack.append( (a // pow(256, 31 - b)) % 256, op=opcode, source=tuple([b_wrapped, a_wrapped]) )

      # shifts a word left by a given amount
      elif opcode == 'SHL':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        if b >= 256:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [b_wrapped, a_wrapped],
              "inputs": [b, a],
              "outputs": 0,
            }
          )
          self.stack.append( 0, op=opcode, source=tuple([b_wrapped, a_wrapped]) )
        else:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [b_wrapped, a_wrapped],
              "inputs": [b, a],
              "outputs": ( a << b ) & self.logic.UINT256_MAX,
            }
          )
          self.stack.append( ( a << b ) & self.logic.UINT256_MAX, op=opcode, source=tuple([b_wrapped, a_wrapped]) )
      
      # shifts a word right by a given amount
      elif opcode == 'SHR':
        [b_wrapped, a_wrapped] = self.stack.pop(2)
        [b, a] = self.stack.unwrap([b_wrapped, a_wrapped])
        if b >= 256:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [b_wrapped, a_wrapped],
              "inputs": [b, a],
              "outputs": 0,
            }
          )
          self.stack.append( 0, op=opcode, source=tuple([b_wrapped, a_wrapped]) )
        else:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [b_wrapped, a_wrapped],
              "inputs": [b, a],
              "outputs": ( a >> b ) & self.logic.UINT256_MAX,
            }
          )
          self.stack.append( ( a >> b ) & self.logic.UINT256_MAX, op=opcode, source=tuple([b_wrapped, a_wrapped]) )

      # calculates the keccak256 hash of a word
      elif opcode == 'SHA3':
        [offset_wrapped, size_wrapped] = self.stack.pop(2)
        [offset, size] = self.stack.unwrap([offset_wrapped, size_wrapped])
        mem = self.memory.read(offset,size)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [offset_wrapped, size_wrapped],
            "inputs": [offset, size],
            "memory": mem.hex(),
            "outputs": int(sha3(mem).hex(),16),
          }
        )
        self.stack.append(int(sha3(mem).hex(),16), op=opcode, source=tuple([offset_wrapped, size_wrapped]))

      # returns the address of the EVM contract
      elif opcode == 'ADDRESS':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": self.address,
          }
        )
        self.stack.append( self.address, source=opcode )

      # returns the balance of the EVM contract
      elif opcode == 'BALANCE':
        [a_wrapped] = self.stack.pop(1)
        [a] = self.stack.unwrap([a_wrapped])
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [a_wrapped],
              "inputs": [a],
              "outputs": web3.eth.get_balance( self.toAddress(a) ),
            }
          )
          self.stack.append(web3.eth.get_balance( self.toAddress(a) ), op=opcode, source=tuple([a_wrapped]))
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [a_wrapped],
              "inputs": [a],
              "outputs": 0,
            }
          )
          self.stack.append( 0, op=opcode, source=tuple([a_wrapped]) )

      # returns the origin of the EVM transaction
      elif opcode == 'ORIGIN':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": self.origin,
          }
        )
        self.stack.append( self.origin, source=opcode )

      # returns the caller of the EVM transaction
      elif opcode == 'CALLER':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": self.caller,
          }
        )
        self.stack.append( self.caller, source=opcode )

      # returns the call value of the EVM transaction in wei
      elif opcode == 'CALLVALUE':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": self.value,
          }
        )
        self.stack.append( self.value, source=opcode )

      # gets the calldata of the EVM transaction at ith offset and a size of 32 bytes
      elif opcode == 'CALLDATALOAD':
        [i_wrapped] = self.stack.pop(1)
        [i] = self.stack.unwrap([i_wrapped])
        if len(hex(self.calldata))%2 == 1:
          safeHex = self.logic.padHex(self.calldata, len(hex(self.calldata)[2:])+1)
        else:
          safeHex = hex(self.calldata)
        callData = bytearray.fromhex(safeHex[2:len(safeHex)-(i*2)])[0:32]
        while len(callData) < 32:
          callData += bytes(1)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [i_wrapped],
            "inputs": [i],
            "outputs": int(callData.hex(), 16),
          }
        )
        self.stack.append ( int(callData.hex(), 16), source=opcode, op=i)

      # gets the size of the calldata of the EVM transaction
      elif opcode == 'CALLDATASIZE':
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": self.logic.byteSize(self.calldata),
            }
          )
          self.stack.append( self.logic.byteSize(self.calldata), source=opcode )
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # copies the calldata to memory
      elif opcode == 'CALLDATACOPY':
        [destOffset_wrapped, offset_wrapped, size_wrapped] = self.stack.pop(3)
        [destOffset, offset, size] = self.stack.unwrap([destOffset_wrapped, offset_wrapped, size_wrapped])

        # if the value isnt even, prepend a 0
        if len(hex(self.calldata))%2 == 1:
          safeHex = self.logic.padHex(self.calldata, len(hex(self.calldata)[2:])+1)
        else:
          safeHex = hex(self.calldata)
 
        # extend memory by the calldatasize
        extended = bytearray.fromhex(safeHex[2:len(safeHex)-(offset*2)])
        self.memory.extend(destOffset, size)
        self.memory.write(destOffset, size, extended)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [destOffset_wrapped, offset_wrapped, size_wrapped],
            "inputs": [destOffset, offset, size],
            "outputs": None,
          }
        )

      # gets the bytecode size of a contract
      elif opcode == 'CODESIZE':
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": self.logic.byteSize(self.bytecode),
            }
          )
          self.stack.append( self.logic.byteSize(self.bytecode), source=opcode )
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # copies the bytecode to memory
      elif opcode == 'CODECOPY':
        [destOffset_wrapped, offset_wrapped, size_wrapped] = self.stack.pop(3)
        [destOffset, offset, size] = self.stack.unwrap([destOffset_wrapped, offset_wrapped, size_wrapped])
        
        # extend memory by the codesize and copy the bytecode to memory
        extended = bytearray.fromhex(hex(self.bytecode)[2:len(hex(self.bytecode))-(offset*2)])
        self.memory.extend(destOffset, size)
        self.memory.write(destOffset, size, extended)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [destOffset_wrapped, offset_wrapped, size_wrapped],
            "inputs": [destOffset, offset, size],
            "outputs": None,
          }
        )
      
      # gets the current gas price in wei
      elif opcode == 'GASPRICE':
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": Web3.toWei(20, 'gwei'),
            }
          )
          self.stack.append(Web3.toWei(20, 'gwei'), source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # gets the codesize of an external account
      elif opcode == 'EXTCODESIZE':
        [target_wrapped] = self.stack.pop(1)
        [target] = self.stack.unwrap([target_wrapped])
        try:
          rawBytecode = web3.eth.get_code(self.toAddress(target))
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [target_wrapped],
              "inputs": [target],
              "outputs": self.logic.byteSize(rawBytecode),
            }
          )
          self.stack.append( self.logic.byteSize(rawBytecode), op=opcode, source=tuple([target_wrapped]) )
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [target_wrapped],
              "inputs": [target],
              "outputs": 0,
            }
          )
          self.stack.append(0, op=opcode, source=tuple([target]))

      # copies the external account's bytecode to memory
      elif opcode == 'EXTCODECOPY':
        [address_wrapped, destOffset_wrapped, offset_wrapped, size_wrapped] = self.stack.pop(3)
        [address, destOffset, offset, size] = self.stack.unwrap([address_wrapped, destOffset_wrapped, offset_wrapped, size_wrapped])
        try:
          rawBytecode = web3.eth.get_code(self.toAddress(address))

          # extend memory by the codesize and copy the bytecode to memory
          extended = bytearray.fromhex(hex(rawBytecode)[:len(hex(rawBytecode))-(offset*2)])
          self.memory.extend(destOffset, size)
          self.memory.write(destOffset, size, extended)
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [address_wrapped, destOffset_wrapped, offset_wrapped, size_wrapped],
              "inputs": [address, destOffset, offset, size],
              "outputs": None,
            }
          )
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [address_wrapped, destOffset_wrapped, offset_wrapped, size_wrapped],
              "inputs": [address, destOffset, offset, size],
              "outputs": None,
            }
          )

      # calculate the returndata size of a call
      elif opcode == 'RETURNDATASIZE':
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": self.logic.byteSize(self.returnData),
            }
          )
          self.stack.append( self.logic.byteSize(self.returnData), source=opcode )
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # copy the return data to memory
      elif opcode == 'RETURNDATACOPY':
        [destOffset_wrapped, offset_wrapped, size_wrapped] = self.stack.pop(3)
        [destOffset, offset, size] = self.stack.unwrap([destOffset_wrapped, offset_wrapped, size_wrapped])
        
        # pad the return data with zeros until the length is even
        if len(hex(self.returnData))%2 == 1:
          safeHex = self.logic.padHex(self.returnData, len(hex(self.returnData)[2:])+1)
        else:
          safeHex = hex(self.returnData)

        # extend the memory and copy the return data to memory
        extended = bytearray.fromhex(safeHex[2:len(safeHex)-(offset*2)])
        self.memory.extend(destOffset, size)
        self.memory.write(destOffset, size, extended)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
             "wrapped": [destOffset_wrapped, offset_wrapped, size_wrapped],
            "inputs": [destOffset, offset, size],
            "outputs": None,
          }
        )

      # get the hash of the code of an external account
      elif opcode == 'EXTCODEHASH':
        [target_wrapped] = self.stack.pop(1)
        [target] = self.stack.unwrap([target_wrapped])
        try:
          rawBytecode = web3.eth.get_code(self.toAddress(target))
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [target_wrapped],
              "inputs": [target],
              "outputs": int(Web3.keccak(rawBytecode).hex(),16),
            }
          )
          self.stack.append( int(Web3.keccak(rawBytecode).hex(),16), op=opcode, source=tuple([target_wrapped]) )
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [target_wrapped],
              "inputs": [target],
              "outputs": 0,
            }
          )
          self.stack.append(0, op=opcode, source=tuple([target_wrapped]))

      # get the hash of the a block 
      elif opcode == 'BLOCKHASH':
        [target_wrapped] = self.stack.pop(1)
        [target] = self.stack.unwrap([target_wrapped])
        try:
          blockhash = web3.eth.get_block(target, full_transactions=False)['hash']
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [target_wrapped],
              "inputs": [target],
              "outputs": int(blockhash.hex() ,16),
            }
          )
          self.stack.append(int(blockhash.hex() ,16), op=opcode, source=tuple([target_wrapped]))
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [target_wrapped],
              "inputs": [target],
              "outputs": 0,
            }
          )
          self.stack.append(0, op=opcode, source=tuple([target_wrapped]))

      # get the coinbase of a block
      elif opcode == 'COINBASE':
        try:
          coinbase = web3.eth.get_block(web3.eth.block_number, full_transactions=False)['miner']
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": int(coinbase, 16),
            }
          )
          self.stack.append(int(coinbase, 16), op=opcode, source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, op=opcode, source=opcode)

      # get the timestamp of a block
      elif opcode == 'TIMESTAMP':
        try:
          timestamp = web3.eth.get_block(web3.eth.block_number, full_transactions=False)['timestamp']
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": timestamp,
            }
          )
          self.stack.append(timestamp, source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # get the number of a block
      elif opcode == 'NUMBER':
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": web3.eth.block_number,
            }
          )
          self.stack.append(web3.eth.block_number, source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # get difficulty of a block
      elif opcode == 'DIFFICULTY':
        try:
          difficulty = web3.eth.get_block(web3.eth.block_number, full_transactions=False)['difficulty']
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": difficulty,
            }
          )
          self.stack.append(difficulty, source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # get gaslimit of a block
      elif opcode == 'GASLIMIT':
        try:
          gasLimit = web3.eth.get_block(web3.eth.block_number, full_transactions=False)['gasLimit']
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": gasLimit,
            }
          )
          self.stack.append(gasLimit, source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # get the current EVM chain ID
      elif opcode == 'CHAINID':
        try:
          chainId = web3.eth.chain_id
          if chainId != None:
            self.stacktrace.append(
              {
                "pc": self.lastInstruction,
                "opcode": opcode,
                "wrapped": None,
                "inputs": None,
                "outputs": chainId,
              }
            )
            self.stack.append(chainId, source=opcode)
          else:
            self.stacktrace.append(
              {
                "pc": self.lastInstruction,
                "opcode": opcode,
                "wrapped": None,
                "inputs": None,
                "outputs": 0,
              }
            )
            self.stack.append(0, source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append(0, source=opcode)

      # get the balance of the current account
      elif opcode == 'SELFBALANCE':
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": web3.eth.get_balance( self.toAddress(self.address) ),
            }
          )
          self.stack.append(web3.eth.get_balance( self.toAddress(self.address) ), source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append( 0, source=opcode )

      # get the basefee of the network
      elif opcode == 'BASEFEE':
        try:
          baseFee = web3.eth.fee_history(1, web3.eth.block_number)['baseFeePerGas'][0]
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": baseFee,
            }
          )
          self.stack.append(baseFee, source=opcode)
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": None,
              "inputs": None,
              "outputs": 0,
            }
          )
          self.stack.append( 0, source=opcode )

      # remove the top item from the stack
      elif opcode == 'POP':
        [out_wrapped] = self.stack.pop(1)
        [out] = self.stack.unwrap([out_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [out_wrapped],
            "inputs": [out],
            "outputs": None,
          }
        )
        
      # load a word from memory at offset
      elif opcode == 'MLOAD':
        [pos_wrapped] = self.stack.pop(1)
        [pos] = self.stack.unwrap([pos_wrapped])
        loaded = int(self.memory.read(pos, 32).hex(), 16)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [pos_wrapped],
            "inputs": [pos],
            "outputs": loaded,
          }
        )
        self.stack.append(loaded, op=opcode, source=tuple([pos_wrapped]))

      # store a value to memory at offset
      elif opcode == 'MSTORE':
        [offset_wrapped, value_wrapped] = self.stack.pop(2)
        [offset, value] = self.stack.unwrap([offset_wrapped, value_wrapped])
        extended = bytearray.fromhex(self.logic.padHex(value, 64)[2:])
        self.memory.extend(offset, 32)
        self.memory.write(offset, 32, extended)
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [offset_wrapped, value_wrapped],
            "inputs": [offset, value],
            "outputs": None,
          }
        )

      # store an 8 byte value to memory at offset
      elif opcode == 'MSTORE8':
        [offset_wrapped, value_wrapped] = self.stack.pop(2)
        [offset, value] = self.stack.unwrap([offset_wrapped, value_wrapped])
        extended = bytearray.fromhex(self.logic.padHex(value, 64)[2:])
        self.memory.extend(offset, 1)
        self.memory.write(offset, 1, bytearray.fromhex(hex(extended[-1])[2:]))
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [offset_wrapped, value_wrapped],
            "inputs": [offset, value],
            "outputs": None,
          }
        )

      # store a value to storage at key
      elif opcode == 'SSTORE':
        [key_wrapped, value_wrapped] = self.stack.pop(2)
        [key, value] = self.stack.unwrap([key_wrapped, value_wrapped])
        self.storage[key] = value
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [key_wrapped, value_wrapped],
            "inputs": [key, value],
            "outputs": None,
          }
        )

      # load a value from storage at key
      elif opcode == 'SLOAD':
        [key_wrapped] = self.stack.pop(1)
        [key] = self.stack.unwrap([key_wrapped])
        try:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [key_wrapped],
              "inputs": [key],
              "outputs": self.storage[key],
            }
          )
          self.stack.append(self.storage[key], op=opcode, source=tuple([key_wrapped]))
        except:
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": [key_wrapped],
              "inputs": [key],
              "outputs": 0,
            }
          )
          self.stack.append(0, op=opcode, source=tuple([key_wrapped]))

      # change the program counter to destination
      elif opcode == 'JUMP':
        [dest_wrapped] = self.stack.pop(1)
        [dest] = self.stack.unwrap([dest_wrapped])
        try:
          if self.assembly[dest]['opcode']['name'] == "JUMPDEST":
            self.instruction = dest
            self.stacktrace.append(
              {
                "pc": self.lastInstruction,
                "opcode": opcode,
                "wrapped": [dest_wrapped],
                "inputs": [dest],
                "outputs": None,
              }
            )
        except:
          self.stacktrace.append(
              {
                "pc": self.lastInstruction,
                "opcode": opcode,
                "wrapped": None,
                "inputs": None,
                "outputs": None,
              }
            )
          
      # change the program counter to destination if the top item on the stack is zero
      elif opcode == 'JUMPI':
        [dest_wrapped, cond_wrapped] = self.stack.pop(2)
        [dest, cond] = self.stack.unwrap([dest_wrapped, cond_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [dest_wrapped, cond_wrapped],
            "inputs": [dest, cond],
            "outputs": None,
          }
        )
        if (self.assembly[dest]['opcode']['name'] == "JUMPDEST") and (cond != 0):
          self.instruction = dest
      
      # get the current program counter
      elif opcode == 'PC':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": self.instruction,
          }
        )
        self.stack.append(self.instruction, source=opcode)

      # get the current size of the EVM memory
      elif opcode == 'MSIZE':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": len(self.memory.getMemory().hex()),
          }
        )
        self.stack.append(len(self.memory.getMemory().hex()), source=opcode)
      
      # get the remaining gas of the current transaction
      elif opcode == 'GAS':
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": None,
            "inputs": None,
            "outputs": self.gas,
          }
        )
        self.stack.append(self.gas, source=opcode)

      # duplicate the nth item of the stack
      elif 'DUP' in opcode:
        dupn = int(opcode.replace('DUP', ''))
        args_wrapped = self.stack.pop(dupn)
        args = self.stack.unwrap(args_wrapped)
        input = copy.deepcopy(args)
        output = []
        args.insert(0, args[-1])
        args_wrapped.insert(0, args_wrapped[-1])
        for i in reversed(range(len(args))):
          output.append(args[i])
          self.stack.append_wrapped(args_wrapped[i])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [args_wrapped],
            "inputs": input,
            "outputs": output,
          }
        )

      # swap the nth item and the top item of the stack
      elif 'SWAP' in opcode:
        swapn = int(opcode.replace('SWAP', ''))
        args_wrapped = self.stack.pop(swapn+1)
        args = self.stack.unwrap(args_wrapped)
        input = copy.deepcopy(args)
        output = []
        temp_wrapped = args_wrapped[-1]
        temp = args[-1]
        args_wrapped[-1] = args_wrapped[0]
        args[-1] = args[0]
        args_wrapped[0] = temp_wrapped
        args[0] = temp
        for i in reversed(range(len(args))):
          output.append(args[i])
          self.stack.append_wrapped(args_wrapped[i])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [args_wrapped],
            "inputs": input,
            "outputs": output,
          }
        )

      # log an event with the given number of topics and data
      elif 'LOG' in opcode:
        try:
          logn = int(opcode.replace('LOG', ''))
          [offset_wrapped, size_wrapped] = self.stack.pop(2)
          [offset, size] = self.stack.unwrap([offset_wrapped, size_wrapped])
          rawTopics = []
          topics = []

          # if the number of topics is greater than 0, get the topics
          if logn > 0:
            rawTopics_wrapped = self.stack.pop(logn)
            rawTopics = self.stack.unwrap(rawTopics_wrapped)
          for topic in rawTopics:
            try:
              topics.append( self.logic.padHex(topic, 64) )
            except Exception as e:
              pass
          
          # read data from memory at offset and size
          mem = bytes(0)
          if len(self.memory.getMemory().hex()) > 0:
            mem = bytes(self.memory.read(offset, size))
            
          # log the event
          self.logEvent(
            {
              "signature": topics[0],
              "topicCount": logn,
              "topics": {
                "indexed": topics[1:],
                "unindexed": [mem.hex()[index : index + 64] for index in range(0, len(mem.hex()), 64)]
              },
            }
          )
          # calculate unindexed topics
          unindexed = []
          for n in range(math.floor(size / 32)):
            unindexed.append(offsetToMemoryName(offset + (n*32)))
        
          # add the log to the stacktrace
          self.stacktrace.append(
            {
              "pc": self.lastInstruction,
              "opcode": opcode,
              "wrapped": rawTopics_wrapped[1:],
              "event": {
                "signature": topics[0],
                "topicCount": logn,
                "topics": {
                  "indexed": topics[1:],
                  "unindexed": unindexed
                },
              }
            }
          )
        except Exception as e:
          pass
        
      # creates a new account with the given code from memory, account address as a hash of bytecode
      elif opcode == "CREATE":
        [value_wrapped, offset_wrapped, size_wrapped] = self.stack.pop(3)
        [value, offset, size] = self.stack.unwrap([value_wrapped, offset_wrapped, size_wrapped])
        addrBytes = bytes(bytearray.fromhex(self.toAddress(self.address)[2:]))
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [value_wrapped, offset_wrapped, size_wrapped],
            "inputs": [value, offset, size],
            "outputs": int((sha3(rlp.encode([addrBytes, 0]))[12:]).hex(), 16),
          }
        )
        self.stack.append( int((sha3(rlp.encode([addrBytes, 0]))[12:]).hex(), 16), op=opcode, source=tuple([value_wrapped, offset_wrapped, size_wrapped]) )

      # creates a new account with the given code from memory, account address as a hash of bytecode with salt
      elif opcode == "CREATE2":
        [value_wrapped, offset_wrapped, size_wrapped, salt_wrapped] = self.stack.pop(3)
        [value, offset, size, salt] = self.stack.unwrap([value_wrapped, offset_wrapped, size_wrapped, salt_wrapped])
        addrBytes = bytes(bytearray.fromhex(self.toAddress(self.address)[2:]))
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [value_wrapped, offset_wrapped, size_wrapped, salt_wrapped],
            "inputs": [value, offset, size, salt],
            "outputs": int((sha3(rlp.encode([addrBytes, 0]))[12:]).hex(), 16),
          }
        )
        self.stack.append( int((sha3(rlp.encode([addrBytes, 0]))[12:]).hex(), 16), op=opcode, source=tuple([value_wrapped, offset_wrapped, size_wrapped, salt_wrapped]) )

      # calls a contract with the given address, value, and data, and saves the return value to memory at retoffset
      elif opcode == 'CALL' or opcode == 'CALLCODE':
        [gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped] = self.stack.pop(7)
        [gas, address, value, argsOffset, argsSize, retOffset, retSize] = self.stack.unwrap([gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped],
            "inputs": [gas, address, value, argsOffset, argsSize, retOffset, retSize],
            "outputs": 1,
          }
        )
        self.stack.append(1, op=opcode, source=tuple([gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped]))

      # calls a contract with the given address, value, and data, and saves the return value to memory at retoffset
      # for delegatecalls, the call can modify the state of the caller
      elif opcode == 'DELEGATECALL' or opcode == 'STATICCALL':
        [gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped] = self.stack.pop(7)
        [gas, address, value, argsOffset, argsSize, retOffset, retSize] = self.stack.unwrap([gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped])
        self.stacktrace.append(
          {
            "pc": self.lastInstruction,
            "opcode": opcode,
            "wrapped": [gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped],
            "inputs": [gas, address, argsOffset, argsSize, retOffset, retSize],
            "outputs": 1,
          }
        )
        self.stack.append(1, op=opcode, source=tuple([gas_wrapped, address_wrapped, value_wrapped, argsOffset_wrapped, argsSize_wrapped, retOffset_wrapped, retSize_wrapped]))
      else:
        pass
    except Exception as e:
      self.stacktrace.append(
        {
          "pc": self.lastInstruction,
          "opcode": "ERROR",
          "inputs": None,
          "outputs": None,
        }
      )
      return (4, str(e), opcode)

  # executes operations on the EVM and returns a stacktrace of the operations
  def trace(self):
    try:
      instructionIndex = list(self.assembly.keys()).index(self.instruction)
      code = self.assembly[self.instruction]
    except:
      instructionIndex = list(self.assembly.keys()).index(str(self.instruction))
      code = self.assembly[str(self.instruction)]
    self.lastInstruction = self.instruction
    self.instruction = (list(self.assembly.keys())[instructionIndex+1])
    
    # executes the operation
    call = self.execute(code['opcode']['name'], code['argument'])
    
    # if the operation returns a value, execution stops
    if call != None:
      return ({
                "trace": self.stacktrace,
                "stack": self.getStack(),
                "logs": self.logs,
                "storage": self.storage,
                "memory": self.memory.getMemory().hex(),
                "returns": call
              })
    return self.trace()