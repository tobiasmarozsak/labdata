import os
import re

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from labdata import config


class Listener(FileSystemEventHandler):
    def __init__(self, func, path, recursive=True):
        self.func = func
        self.path = os.fsdecode(path)
        self.recursive = recursive
        self.observer = None

    def start(self):
        if self.observer is None:
            self.observer = Observer()
            self.observer.schedule(self, self.path, recursive=self.recursive)
            self.observer.start()

    def stop(self):
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def on_moved(self, event):
        if re.fullmatch(
            config.DATA_FILE_PATTERN,
            os.path.basename(event.dest_path),
        ):
            self.func({
                "src": event.src_path,
                "dst": event.dest_path,
                "type": event.event_type,
            })


REGISTRY = {}


def connect(func, path, recursive=True):
    if func not in REGISTRY:
        listener = Listener(func, path, recursive=recursive)
        REGISTRY[func] = listener
        listener.start()


def disconnect(func):
    if func in REGISTRY:
        REGISTRY.pop(func).stop()
