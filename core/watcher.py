import os
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class SharronWatchHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.recent_events = {}
        self.debounce_interval = 1.0

    def _is_spam_event(self, file_path: str) -> bool:
        """Determines if this event is firing too quickly after a previous one."""
        current_time = time.time()
        
        if file_path in self.recent_events:
            time_since_last_event = current_time - self.recent_events[file_path]
            if time_since_last_event < self.debounce_interval:
                return True # It's rapid-fire ignore it
                
        self.recent_events[file_path] = current_time
        return False

    def on_modified(self, event):
        if event.is_directory or self._is_spam_event(event.src_path):
            return
        print(f"📝 File Modified: {os.path.basename(event.src_path)}")

    def on_created(self, event):
        if event.is_directory or self._is_spam_event(event.src_path):
            return
        print(f"🆕 File Created: {os.path.basename(event.src_path)}")

    def on_moved(self, event):
        if event.is_directory:
            return

        destination_name = os.path.basename(event.dest_path)

        print(f"📝 File Modified (via swap): {destination_name}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        print(f"🗑️ File Deleted: {os.path.basename(event.src_path)}")

class DirectoryWatcher:
    def __init__(self, path_to_watch: str):
        """
        Initializes the file system monitor.
        :param path_to_watch: Absolute path to the local SharronDrive directory
        """
        self.path = path_to_watch
        self.event_handler = SharronWatchHandler()
        self.observer = Observer()

    def start(self):
        """Schedules the watcher and launches the background OS worker thread."""
        # recursive=False means it only watches the top-level folder. 
        # TODO: support subfolders!
        self.observer.schedule(self.event_handler, self.path, recursive=False)
        self.observer.start()
        print(f"👁️  Local File Intelligence monitoring: {self.path}")

    def stop(self):
        """Safely stops the background thread and releases OS handles."""
        self.observer.stop()
        self.observer.join()
