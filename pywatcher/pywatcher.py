from watchdog.utils.patterns import filter_paths
from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent
from .utilities import Snapshot
from .event_handler import PatternEventHandler
from .config import settings
import time

class PyWatcher():
    def __init__(self) -> None:
        self.handler = PatternEventHandler()

    def start(self):

        unprocessedEvent = Snapshot(settings.default.path).resume()
        if unprocessedEvent is not Snapshot.FIRST_RUN_MSG:
            print("Resume from last run")
            for event in unprocessedEvent:
                self.handler.on_created(event) if isinstance(event, FileCreatedEvent) else None
            Snapshot(settings.default.path).shot()
        else:
            print("First run detected. Watching...")
            paths = Snapshot(settings.default.path).shot().paths
            if settings.default.ignore_directories:
                for event in filter_paths(paths, settings.default.patterns, settings.default.ignore_patterns, settings.default.case_sensitive):
                    self.handler.on_created(FileCreatedEvent(event))
            else:
                for event in paths:
                    self.handler.on_created(FileCreatedEvent(event))

        observer = Observer()
        observer.schedule(self.handler, settings.default.path, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        # CTRL + C to stop
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == "__main__":
    PyWatcher().start()