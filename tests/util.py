import os
import pathlib

from subprocess import DEVNULL, STDOUT, check_call


from heimdall.lib.utils.io import *

# creates a test environment for the given test name with python3's virtualenv
def createTestEnvironment(test_name):
    env_path = f'{pathlib.Path(__file__).parent.resolve()}/envs/{test_name}'
    makePath(env_path)
    
    check_call(['python3', '-m', 'venv', 'env'], stdout=DEVNULL, stderr=STDOUT, cwd=env_path)
    
    return env_path

# deletes the test environment
def wipeTestEnvironment(path):    
    os.rmdir(path)