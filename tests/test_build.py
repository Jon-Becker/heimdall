import pathlib

def test_virtualenv(virtualenv):
  assert 'python' in virtualenv.python
    
def test_installing(virtualenv):
  if 'eth-heimdall' in [i for i in virtualenv.installed_packages()]:
    pass
  else:
    virtualenv.run(f'pip install -e {pathlib.Path(__file__).parent.parent.resolve()}')
  
  assert 'eth-heimdall' in [i for i in virtualenv.installed_packages()]