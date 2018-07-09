#!/usr/bin/env python

import sys
import os
import errno
import tarfile
import glob
from stat import S_IRWXU, S_IRWXG

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def force_symlink(file1, file2):
    try:
        os.symlink(file1, file2)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(file2)
            os.symlink(file1, file2)

with cd('/home/ndeploy/sdap-search'):
  tar_file = next(f_name for f_name in glob.glob(sys.argv[1]) if os.path.isfile(f_name))
  with tarfile.open(tar_file) as tar:
    tar.extractall(path='/home/ndeploy/sdap-search/')

  extracted_dir = os.path.join('/home/ndeploy/sdap-search/', os.path.basename(tar_file).strip('.tar.gz'))
  os.chmod(os.path.join(extracted_dir, 'bin', 'mudrod-engine'), S_IRWXU | S_IRWXG)

  force_symlink(extracted_dir, 'mudrod-engine')

  try:
      os.mkdir('bin')
  except:
      pass


  force_symlink(os.path.join(extracted_dir, 'bin', 'mudrod-engine'), '/home/ndeploy/sdap-search/bin/mudrod-engine')
