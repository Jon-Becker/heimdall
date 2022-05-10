class Stack:
  def __init__(self, _stack=[]):
    self.stack = _stack
    self.trace = []

  def peek(self, n=1):
    res = []
    for i in range(1, n+1):
      res.append(self.stack[i-1:i][0])
    return res

  def pop(self, n=1):
    res = []
    for i in range(n):
      res.append(self.stack.pop())
    return res

  def append_wrapped(self, wrapped):
    self.stack.append(wrapped)

  def append(self, value, op=None, source=None):
    self.stack.append((op, value, source,))
    return self.stack

  def wrap(self, value, op=None, source=None):
    return (op, value, source, )

  def unwrap(self, values):
    res = []
    for wrapped in values:
      res.append(wrapped[1])
    return res
    
  def prepend(self, value):
    self.stack.insert(0, value)

  def getStack(self):
    return self.stack