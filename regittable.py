import argparse, json, munch
import logging, time, sys
import os, shutil

from pathlib import PurePath, Path
from watchdog.observers import Observer
from watchdog.events import *


def safejoin(path1, path2):
  path1 = PurePath(PurePath(path1).as_posix())
  path2 = PurePath(PurePath(path2).as_posix())
  return Path(path1.joinpath(path2))

class ConfigLoader(munch.Munch):
  def __init__(self, config_path):
    with open(config_path, 'r') as config_file:
      config_json = json.load(config_file)
    munch.Munch.__init__(self, config_json)
    self.files = munch.munchify(self.files)


class RegitHandler(FileSystemEventHandler):
  """
  The RegitHandler looks for changes to the specific files
  that we are interested in, and doing specific actions based on that
  """
  def __init__(self, config, case_sensitive=True):
    FileSystemEventHandler.__init__(self)
    self.update_config(config)
  
  def update_config(self, config):
    self._watchpath = config.watch_path
    self._files = config.files

  def on_created(self, event):
    super().on_modified(event)
    what = 'directory' if event.is_directory else 'file'
    logging.info("Modified %s: %s", what, event.src_path)

  def on_modified(self, event):
    super().on_modified(event)
    what = 'directory' if event.is_directory else 'file'
    logging.info("Modified %s: %s", what, event.src_path)
    src = Path(event.src_path)
    if not src.exists():
      logging.info(f"{src} does not exist, maybe already moved?")
    file = self.first_match(event)
    if "none" == file.git_mode:
      destination = safejoin(self._watchpath, file.destination)
      if '*' in destination.name:
        destination = destination.with_name(file.name)

      print ("Moving file to ", destination)
      try:
        src.replace(destination)
      except:
        logging.info("Warning: source probably does not exist")
      
  def first_match(self, event):
    for file in self._files:
      match = 0
      if hasattr(event, 'src_path'):
        match += file.name in event.src_path
      if hasattr(event, 'dest_path'):
        match += file.name in event.dest_path
      if match > 0: 
        return file

  def event_has_match(self, event):
    match = 0
    if hasattr(event, 'src_path'):
      match += sum([f"{file.name}" in f"{event.src_path}" for file in self._files]) > 0
    if hasattr(event, 'dest_path'):
      match += sum([f"{file.name}" in f"{event.dest_path}" for file in self._files]) > 0
    # print (self._files[0].name, event.src_path, self._files[0].name in event.src_path)
    return match > 0

  def dispatch(self, event):
    """Dispatches events to the appropriate methods.

    :param event:
        The event object representing the file system event.
    :type event:
        :class:`FileSystemEvent`
    """
    if self.event_has_match(event):
      self.on_any_event(event)
      _method_map = {
        EVENT_TYPE_MODIFIED: self.on_modified,
        EVENT_TYPE_MOVED: self.on_moved,
        EVENT_TYPE_CREATED: self.on_created,
        EVENT_TYPE_DELETED: self.on_deleted,
      }
      event_type = event.event_type
      _method_map[event_type](event)


def reload_config(config_path):
  return ConfigLoader(config_path)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Run a watchdog to sync reMarkable files with folders or git repositories.\nhttps://github.com/keerthik/regittable")
  parser.add_argument('config_path', nargs='?', type=Path, default="regittable-config.json", help="The config file specifying what to watch and what to do with changes")
  parser.add_argument('-v', dest='verbose', action='store_true', help="Enable verbose logging in the process window, if open")
  args = parser.parse_args()

  if args.verbose:
    print ("Verbose logging enabled...")
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')

  config = reload_config(args.config_path)
  # event_handler = LoggingEventHandler()
  logging.info(f"Listening at {config.watch_path} for new files")
  src_handler = RegitHandler(config)
  src_observer = Observer()
  src_observer.schedule(src_handler, config.watch_path, recursive=False)
  src_observer.start()

  try:
    while True:
      print ("i sleep")
      time.sleep(1)
  except KeyboardInterrupt:
    print ("i stop")
    src_observer.stop()

  src_observer.join()