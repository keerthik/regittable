import munch, json
from pathlib import PurePath, Path

class JSONLoader(munch.Munch):
  def __init__(self, config_path):
    with open(config_path, 'r') as config_file:
      config_json = json.load(config_file)
    munch.Munch.__init__(self, config_json)

  def nested_object(self, param_name):
    self[param_name] = munch.munchify(self[param_name])


def safepath(inpath):
  return Path(PurePath(inpath).as_posix()).expanduser().resolve()

def safejoin(path1, path2):
  path1 = PurePath(PurePath(path1).as_posix())
  path2 = PurePath(PurePath(path2).as_posix())
  return Path(path1.joinpath(path2))


