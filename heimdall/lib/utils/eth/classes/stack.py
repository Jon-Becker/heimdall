class Stack:
  def __init__(self, _stack=[]):
    self.stack = _stack
    self.trace = []

  # look at the next n values on the stack without modifying the stack
  def peek(self, n=1):
    res = []
    for i in range(1, n+1):
      res.append(self.stack[i-1:i][0])
    return res

  # remove the top n values from the stack
  def pop(self, n=1):
    res = []
    for i in range(n):
      res.append(self.stack.pop())
    return res

  # appends a wrapped value to the stack
  def append_wrapped(self, wrapped):
    self.stack.append(wrapped)

  # appends an operation to the stack
  def append(self, value, op=None, source=None):
    self.stack.append((op, value, source,))
    return self.stack

  # returns the wrapped value of an operation, which saves sources and operations performed on the stack
  def wrap(self, value, op=None, source=None):
    return (op, value, source, )

  # unwraps the `value` of an operation
  def unwrap(self, values):
    res = []
    for wrapped in values:
      res.append(wrapped[1])
    return res
    
  # insert an operation into the stack at the end of the stack
  def prepend(self, value):
    self.stack.insert(0, value)

  # returns the stack
  def getStack(self):
    return self.stack