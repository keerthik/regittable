import os
from subprocess import check_output

class GitOps:
  def __init__(self, repopath):
    self.wd_cache = os.getcwd()
    self.wd = repopath

  def cmd(self, cmd):
    os.chdir(self.wd)
    result = check_output(cmd, shell=True)
    print(result.decode())
    os.chdir(self.wd_cache)
    return result