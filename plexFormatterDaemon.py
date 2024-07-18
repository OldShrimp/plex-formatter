import logging
import daemon
import os
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from time import sleep
import plexFormatter

class CopyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(f"File {event.src_path} triggered {event.event_type}")
    def on_created(self, event):
        plexFormatter.processPath(event.src_path, plexFormatter.config.dest)
class MoveHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(f"File {event.src_path} triggered {event.event_type}")
    def on_created(self, event):
        plexFormatter.processPath(event.src_path, plexFormatter.config.dest, move=True)

# Create observer and event handler
observer = Observer()
copy_handler = CopyHandler()
move_handler = MoveHandler()

# Set up observer to watch specified directories and do initial scan
for path in plexFormatter.config.copysrc:
    print(path)
    observer.schedule(copy_handler, path)
    plexFormatter.processPath(path, plexFormatter.config.dest)
for path in plexFormatter.config.movesrc:
    print(path)
    observer.schedule(move_handler, path)
    plexFormatter.processPath(path, plexFormatter.config.dest)

observer.start()
print("observer started")
try:
    while True:
        sleep(10)
except KeyboardInterrupt:
    observer.stop()

observer.join()
