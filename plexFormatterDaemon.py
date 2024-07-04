import logging
import daemon
import os
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from time import sleep
import plexFormatter

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(f"File {event.src_path} triggered {event.event_type}")
    def on_created(self, event):
        plexFormatter.processPath(event.src_path, plexFormatter.config.dest)

# Create observer and event handler
observer = Observer()
event_handler = MyHandler()

# Set up observer to watch a specific directory
directory_to_watch = plexFormatter.config.src
observer.schedule(event_handler, directory_to_watch)

# scan any existing files
plexFormatter.processPath(plexFormatter.config.src, plexFormatter.config.dest)

observer.start()

try:
    while True:
        sleep(10)
except KeyboardInterrupt:
    observer.stop()

observer.join()
