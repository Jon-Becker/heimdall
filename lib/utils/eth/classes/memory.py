class Memory:
  def __init__(self):
    self.store = bytes(0)

  def safeCiel(self, value, cieling):
    r = value % cieling
    if r == 0:
      return value
    return value + cieling - r

  def extend(self, offset, size):
    if size == 0:
      return
    newSize = self.safeCiel(offset + size, 32)
    sizeDifference = newSize - len(self.store)
    if sizeDifference > 0:
      self.store = self.store + bytes(sizeDifference)

  def write(self, offset, size, bufferval):
    if ( ( len(bufferval) == size ) and ( offset + size <= len(self.store) ) ):
      temp = bytearray.fromhex(self.store.hex())
      for i in range(size):
        temp[offset + i] = bufferval[i]
      self.store = bytes(temp)

  def read(self, offset, size):
    result = bytearray()
    temp = bytearray.fromhex(self.store.hex())
    loaded = temp[offset:offset+size]
    result += loaded
    if len(loaded) < size:
      result += bytes(size-len(loaded))
    return result


  def getMemory(self):
    return self.store
