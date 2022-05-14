from ..logic import listContainsList

def resolve(int):
  versions = ['Homestead', 'Byzantium', 'Constantinople', 'Istanbul', 'London', 'ArrowGlacier']
  return versions[int]

def detectVersion(assembly, args):
  versions = ['Homestead', 'Byzantium', 'Constantinople', 'Istanbul', 'London', 'ArrowGlacier']
  assemblyFlat = [assembly[pc]['opcode']['name'] for pc in assembly]
  min = [0, '0.1.0']
  max = [4, '0.8.14']
  
  if not listContainsList(['REVERT', 'RETURNDATASIZE', 'RETURNDATACOPY'], assemblyFlat):
    max[0] = 1
  elif not listContainsList(['SHL', 'SHR', 'SAR', 'EXTCODEHASH'], assemblyFlat):
    min[0] = 1
    max[0] = 2
  elif not listContainsList(['CREATE2', 'CHAINID', 'SELFBALANCE'], assemblyFlat):
    min[0] = 2
    max[0] = 3
  elif not listContainsList(['BASEFEE'], assemblyFlat): 
    min[0] = 3
    max[0] = 4
  
  
  if listContainsList(['BASEFEE'], assemblyFlat):
    max[1] = '0.8.14'
    min[1] = '0.8.7'
  elif listContainsList(['EXTCODEHASH'], assemblyFlat):
    max[1] = '0.5.0'
    min[1] = '0.4.12'
  elif listContainsList(['RETURNDATASIZE', 'RETURNDATACOPY', 'CREATE2', 'STATICCALL'], assemblyFlat):
    max[1] = '0.4.12'
    min[1] = '0.4.10'
  elif listContainsList(['REVERT'], assemblyFlat):
    max[1] = '0.4.10'
    min[1] = '0.4.7'
  elif listContainsList(['SHL', 'SHR', 'SAR'], assemblyFlat):
    max[1] = '0.4.7'

  return (min, max)