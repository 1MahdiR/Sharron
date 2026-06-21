import os
import time
import base64
from core.serializer import EventSerializer

def request_file_fallback(mesh_engine, sender_ip: str, file_name: str) -> bool:
    print(f"🔄 Triggering fallback request to {sender_ip} for missing file: {file_name}")
    request_payload = {
        "action": "FILE_REQUEST",
        "file_name": file_name,
        "timestamp": time.time()
    }
    return mesh_engine.send_secure_payload(sender_ip, request_payload)

def handle_incoming_file_request(mesh_engine, peer_ip: str, requested_file: str, sync_path: str):
    full_path = os.path.join(sync_path, requested_file)
    
    if os.path.exists(full_path) and os.path.isfile(full_path):
        print(f"📤 Fulfilling fallback request for {requested_file}. Sending content...")
        fallback_payload = EventSerializer.serialize(
            action="MODIFIED",
            src_name=requested_file,
            dest_name=None,
            sync_path=sync_path
        )
        mesh_engine.send_secure_payload(peer_ip, fallback_payload)
    else:
        print(f"⚠️ Requested file {requested_file} missing locally. Notifying peer.")
        nack_payload = {
            "action": "FILE_NOT_FOUND",
            "file_name": requested_file,
            "timestamp": time.time()
        }
        mesh_engine.send_secure_payload(peer_ip, nack_payload)

def on_remote_file_received(payload, sender_ip: str, mesh_engine):
    from config.settings import Settings
    action = payload["action"]
    app_settings = Settings()
    
    if action == "FILE_REQUEST":
        handle_incoming_file_request(mesh_engine, sender_ip, payload["file_name"], app_settings.sync_path)
        return

    if action == "FILE_NOT_FOUND":
        print(f"❌ [Action Aborted] Remote peer does not have '{payload['file_name']}'. Dropping operation.")
        return

    if action == "MOVED":
        src_name = payload["src_name"]
        dest_name = payload["dest_name"]
        full_src_path = os.path.join(app_settings.sync_path, src_name)
        
        if not os.path.exists(full_src_path):
            print(f"⚠️ Cannot apply [MOVED] event. Source '{src_name}' is missing.")
            request_file_fallback(mesh_engine, sender_ip, dest_name)
            return
            
        full_dest_path = os.path.join(app_settings.sync_path, dest_name)
        dest_dir = os.path.dirname(full_dest_path)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
            
        os.rename(full_src_path, full_dest_path)
        print(f"🚚 File moved locally: {full_dest_path}")
            
    elif action in ("CREATED", "MODIFIED"):
        file_name = payload["file_name"]
        file_data = payload.get("file_data")
        
        if not file_data:
            print(f"⚠️ Received [{action}] payload for '{file_name}' with no file data.")
            request_file_fallback(mesh_engine, sender_ip, file_name)
            return
            
        full_path = os.path.join(app_settings.sync_path, file_name)
        parent_dir = os.path.dirname(full_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        raw_bytes = base64.b64decode(file_data.encode('utf-8'))
        with open(full_path, "wb") as f:
            f.write(raw_bytes)
            f.flush()
            os.fsync(f.fileno())
        print(f"💾 File written to disk: {full_path}")
        
    elif action == "DELETED":
        file_name = payload["file_name"]
        full_path = os.path.join(app_settings.sync_path, file_name)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"🗑️ File deleted locally: {file_name}")