import argparse, pathlib, json, munch
import logging, time, sys

from watchdog.observers import Observer
from watchdog.events import *

class RemarkableHandler(FileSystemEventHandler):
  """
  The RemarkableHandler looks for changes to the filetypes that 
  """
  
  def __init__(self, files, case_sensitive=True):
    self.files = files
    regex =  [ fr"^{file.name}" for file in self.files ]
    print (f"Looking for all files fitting regexs: {regex}")
    FileSystemEventHandler.__init__(self)

  def on_created(self, event):
    super().on_modified(event)
    what = 'directory' if event.is_directory else 'file'
    logging.info("Modified %s: %s", what, event.src_path)

  def on_modified(self, event):
    # check if changed file is config
    # move file to target folder
    # clear source file
    super().on_modified(event)
    what = 'directory' if event.is_directory else 'file'
    logging.info("Modified %s: %s", what, event.src_path)

  def event_has_match(self, event):
    match = 0
    if hasattr(event, 'src_path'):
      match += sum([f"{file.name}" in f"{event.src_path}" for file in self.files]) > 0
    if hasattr(event, 'dest_path'):
      match += sum([f"{file.name}" in f"{event.dest_path}" for file in self.files]) > 0
    # print (self.files[0].name, event.src_path, self.files[0].name in event.src_path)
    return match

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


class ConfigLoader(munch.Munch):
  def __init__(self, config_path):
    with open(config_path, 'r') as config_file:
      config_json = json.load(config_file)
    munch.Munch.__init__(self, config_json)
    self.files = munch.munchify(self.files)

def reload_config(config_path):
  return ConfigLoader(config_path)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Run a watchdog to sync reMarkable files with folders or git repositories.\nhttps://github.com/keerthik/regittable")
  parser.add_argument('config_path', nargs='?', type=pathlib.Path, default="./regittable-config.json", help="The config file specifying what to watch and what to do with changes")
  parser.add_argument('-v', dest='verbose', action='store_true', help="Enable verbose logging in the process window, if open")
  args = parser.parse_args()

  if args.verbose:
    print ("Verbose logging enabled...")
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')

  config = reload_config(args.config_path)
  # event_handler = LoggingEventHandler()
  remarkable_handler = RemarkableHandler(config.files)

  print ("Listening at ", config.watch_path)
  file_observer = Observer()
  file_observer.schedule(remarkable_handler, config.watch_path, recursive=False)
  file_observer.start()
  try:
    while True:
      print ("i sleep")
      time.sleep(1)
  except KeyboardInterrupt:
    print ("i stop")
    file_observer.stop()
  file_observer.join()


