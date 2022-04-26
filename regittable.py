import argparse, json, munch
import logging, time, sys
import shutil

from pathlib import PurePath, Path
from watchdog.observers import Observer
from watchdog.events import *


def safepath(inpath):
  return Path(PurePath(inpath).as_posix()).expanduser().resolve()

def safejoin(path1, path2):
  path1 = PurePath(PurePath(path1).as_posix())
  path2 = PurePath(PurePath(path2).as_posix())
  return Path(path1.joinpath(path2))

class ConfigLoader(munch.Munch):
  def __init__(self, config_path):
    with open(config_path, 'r') as config_file:
      config_json = json.load(config_file)
    munch.Munch.__init__(self, config_json)
    self.watch_path = safepath(self.watch_path)
    for file in self.files:
      file.setdefault('git_mode',     "none")
      file.setdefault('auto_delete',  "false")
      file.setdefault('consumed',     False)
    self.files = munch.munchify(self.files)


class RegitHandler(FileSystemEventHandler):
  """
  The RegitHandler looks for changes to the specific files
  that we are interested in, and doing specific actions based on that
  """

  def log_event(self, event):
    _event_map = {
      EVENT_TYPE_MODIFIED: "Modified",
      EVENT_TYPE_MOVED: "Moved",
      EVENT_TYPE_CREATED: "Created",
      EVENT_TYPE_DELETED: "Deleted",
    }
    what = 'directory' if event.is_directory else 'file'
    matching = ''
    if self.event_has_match(event):
      matching = 'consumed' if self.first_match(event).consumed else 'not consumed yet'
    else:
      matching = 'but not a match'
    logging.debug("%s: %s @%s, %s", _event_map[event.event_type], what, event.src_path, matching)

  def __init__(self, config, case_sensitive=True):
    FileSystemEventHandler.__init__(self)
    self._ignore_directories=True
    self.update_config(config)

  @property
  def ignore_directories(self):
    """
    (Read-only)
    ``True`` if directories should be ignored; ``False`` otherwise.
    """
    return self._ignore_directories
  
  def update_config(self, config):
    self._watchpath = config.watch_path
    self._files = config.files

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
    if self.ignore_directories and event.is_directory:
      return False
    if hasattr(event, 'src_path'):
      match += sum([f"{file.name}" in f"{event.src_path}" for file in self._files]) > 0
    if hasattr(event, 'dest_path'):
      match += sum([f"{file.name}" in f"{event.dest_path}" for file in self._files]) > 0
    # print (self._files[0].name, event.src_path, self._files[0].name in event.src_path)
    return match > 0

  def consume_event(self, event):
    src = Path(event.src_path)
    if not src.exists():
      return
    file = self.first_match(event)
    if file.consumed:
      logging.info("[regit] Resetting file status")
      file.consumed = False
      return
    destination = safejoin(self._watchpath, file.destination)
    if '*' in destination.name:
      destination = destination.with_name(file.name)
    # try:
    _do_move = "true"==file.auto_delete.lower()
    src.replace(destination) if _do_move else shutil.copyfile(src, destination)
    action = 'moving' if _do_move else 'copying'
    logging.info(f"[regit] {action} file to {destination}...")
    if "none" == file.git_mode.lower():
      logging.info("[regit] ...finished")
    file.consumed = True
    # except:
    #   logging.debug("Warning: source probably does not exist")

  def on_created(self, event):
    super().on_created(event)
    self.log_event(event)
    self.consume_event(event)

  def on_moved(self, event):
    super().on_moved(event)
    self.log_event(event)
    self.consume_event(event)

  def on_deleted(self, event):
    super().on_deleted(event)
    # self.log_event(event)

  def on_modified(self, event):
    super().on_modified(event)
    self.log_event(event)
    self.consume_event(event)
      
  def dispatch(self, event):
    """Dispatches events to the appropriate methods.

    :param event:
        The event object representing the file system event.
    :type event:
        :class:`FileSystemEvent`
    """
    # if self.event_has_match(event):
    self.on_any_event(event)

    if self.event_has_match(event):
      self.log_event(event)
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
    logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s - %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')

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
      logging.debug("i sleep")
      time.sleep(5)
  except KeyboardInterrupt:
    logging.debug("i stop")
    src_observer.stop()

  src_observer.join()