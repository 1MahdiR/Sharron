import os
import time
import base64

class EventSerializer:
    @staticmethod
    def _wait_for_file_stability(full_path: str, timeout=2.0) -> bool:
        if not os.path.exists(full_path):
            return False
        start_time = time.time()
        last_size = -1
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(full_path)
                if current_size == last_size and current_size >= 0:
                    with open(full_path, 'rb') as f:
                        pass
                    return True
                last_size = current_size
            except (OSError, IOError):
                pass
            time.sleep(0.1)
        return False

    @classmethod
    def serialize(cls, action: str, src_name: str, dest_name: str, sync_path: str) -> dict:
        payload = {
            "action": action,
            "timestamp": time.time(),
            "src_name": None,
            "dest_name": None,
            "file_name": None,
            "file_data": None
        }

        if action == "MOVED":
            payload["src_name"] = src_name
            payload["dest_name"] = dest_name
            payload["file_data"] = None

        elif action in ("CREATED", "MODIFIED"):
            payload["file_name"] = src_name
            full_src_path = os.path.join(sync_path, src_name)
            if cls._wait_for_file_stability(full_src_path):
                try:
                    with open(full_src_path, "rb") as f:
                        payload["file_data"] = base64.b64encode(f.read()).decode('utf-8')
                except Exception:
                    payload["file_data"] = ""
            else:
                payload["file_data"] = ""

        elif action == "DELETED":
            payload["file_name"] = src_name
            payload["file_data"] = None

        else:
            payload["file_name"] = src_name

        return payload