import os
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class SharronWatchHandler(FileSystemEventHandler):
    def __init__(self, root_path, change_callback):
        super().__init__()
        self.root_path = os.path.abspath(root_path)
        self.change_callback = change_callback
        self.recent_events = {}
        self.debounce_interval = 1.0

    def _is_spam_event(self, file_path: str) -> bool:
        current_time = time.time()
        if file_path in self.recent_events:
            time_since_last_event = current_time - self.recent_events[file_path]
            if time_since_last_event < self.debounce_interval:
                return True
        self.recent_events[file_path] = current_time
        return False

    def on_created(self, event):
        if event.is_directory or self._is_spam_event(event.src_path):
            return
        rel_path = os.path.relpath(event.src_path, self.root_path)
        if self.change_callback:
            self.change_callback(event)
        else:
            print(f"CREATE signal detected: {rel_path}")

    def on_modified(self, event):
        if event.is_directory or self._is_spam_event(event.src_path):
            return
        rel_path = os.path.relpath(event.src_path, self.root_path)
        if self.change_callback:
            self.change_callback(event)
        else:
            print(f"MODIFY signal detected: {rel_path}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        rel_path = os.path.relpath(event.src_path, self.root_path)
        if self.change_callback:
            self.change_callback(event)
        else:
            print(f"DELETE signal detected: {rel_path}")

    def on_moved(self, event):
        if event.is_directory:
            return
        rel_dest = os.path.relpath(event.dest_path, self.root_path)
        if self.change_callback:
            self.change_callback(event)
        else:
            rel_src = os.path.relpath(event.src_path, self.root_path)
            print(f"MOVE signal detected: {rel_src} -> {rel_dest}")

class DirectoryWatcher:
    def __init__(self, path_to_watch: str, change_callback):
        self.path = os.path.abspath(path_to_watch)
        self.event_handler = SharronWatchHandler(self.path, change_callback)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, self.path, recursive=True)
        self.observer.start()
        print(f"👁️  Local File Intelligence monitoring: {self.path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()