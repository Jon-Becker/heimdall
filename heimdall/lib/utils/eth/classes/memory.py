class Memory:
  def __init__(self):
    self.store = bytes(0)

  # safely calculate the cieling of a value to the uint256 maximum
  def safeCiel(self, value, cieling):
    r = value % cieling
    if r == 0:
      return value
    return value + cieling - r

  # extend memory by the given size after offset
  def extend(self, offset, size):
    if size == 0:
      return
    newSize = self.safeCiel(offset + size, 32)
    sizeDifference = newSize - len(self.store)
    if sizeDifference > 0:
      self.store = self.store + bytes(sizeDifference)

  # add a value to the memory at the given offset, with a fixed size.
  def write(self, offset, size, bufferval):
    if ( ( len(bufferval) == size ) and ( offset + size <= len(self.store) ) ):
      temp = bytearray.fromhex(self.store.hex())
      for i in range(size):
        temp[offset + i] = bufferval[i]
      self.store = bytes(temp)

  # read a value from the memory at the given offset, with a fixed size. 
  def read(self, offset, size):
    result = bytearray()
    temp = bytearray.fromhex(self.store.hex())
    loaded = temp[offset:offset+size]
    result += loaded
    
    # if memory length after offset is less than size, we append null bytes to the end of the memory.
    if len(loaded) < size:
      result += bytes(size-len(loaded))
    return result

  # returns the memory object
  def getMemory(self):
    return self.store
