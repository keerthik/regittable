import os
from subprocess import check_output

tasterepo = "D:\\dev\\narrative\\tastegame"

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

ops = GitOps(tasterepo)
ops.cmd("git status")

# os.chdir(tasterepo)
# print (check_output("git status", shell=True).decode())

