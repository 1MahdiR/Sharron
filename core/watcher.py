import os
import time
import platform
from threading import Lock
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class SharronWatchHandler(FileSystemEventHandler):
    def __init__(self, root_path, change_callback):
        super().__init__()
        self.root_path = os.path.abspath(root_path)
        self.change_callback = change_callback
        self.recent_events = {}
        self.ignored_paths = {}
        self.debounce_interval = 1.0
        self._lock = Lock()

    def ignore_path(self, full_path: str):
        with self._lock:
            self.ignored_paths[os.path.abspath(full_path)] = time.time()

    def unignore_path(self, full_path: str):
        with self._lock:
            self.ignored_paths.pop(os.path.abspath(full_path), None)

    def _is_hidden(self, path: str) -> bool:
        name = os.path.basename(path)
        if name.startswith('.'):
            return True
        if platform.system() == "Windows":
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
                if attrs != -1 and (attrs & 2):
                    return True
            except Exception:
                pass
        return False

    def _should_skip(self, file_path: str) -> bool:
        abs_path = os.path.abspath(file_path)
        current_time = time.time()

        if self._is_hidden(abs_path):
            return True

        if abs_path in self.ignored_paths:
            try:
                disk_mtime = os.path.getmtime(abs_path)
                lock_time = self.ignored_paths[abs_path]
                if disk_mtime > lock_time + 0.05:
                    return False
            except OSError:
                pass
            return True

        if abs_path in self.recent_events:
            time_since_last_event = current_time - self.recent_events[abs_path]
            if time_since_last_event < self.debounce_interval:
                return True

        self.recent_events[abs_path] = current_time
        return False

    def on_created(self, event):
        if event.is_directory:
            return
        with self._lock:
            if self._should_skip(event.src_path):
                return
        rel_path = os.path.relpath(event.src_path, self.root_path)
        if self.change_callback:
            self.change_callback(event)
        else:
            print(f"CREATE signal detected: {rel_path}")

    def on_modified(self, event):
        if event.is_directory:
            return
        with self._lock:
            if self._should_skip(event.src_path):
                return
        rel_path = os.path.relpath(event.src_path, self.root_path)
        if self.change_callback:
            self.change_callback(event)
        else:
            print(f"MODIFY signal detected: {rel_path}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        with self._lock:
            if self._should_skip(event.src_path):
                return
        rel_path = os.path.relpath(event.src_path, self.root_path)
        if self.change_callback:
            self.change_callback(event)
        else:
            print(f"DELETE signal detected: {rel_path}")

    def on_moved(self, event):
        if event.is_directory:
            return
        with self._lock:
            if self._should_skip(event.dest_path):
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