import socket
import time
import os
import base64

from config.settings import Settings
from core.crypto import CryptoEngine
from core.discovery import DiscoveryMesh
from core.mesh import MeshNetwork
from core.watcher import DirectoryWatcher
from core.serializer import EventSerializer

mesh_engine = None

def on_peer_found(ip_address, device_name):
    """Fires automatically when a peer is discovered via UDP heartbeat."""
    print(f"\n✨ Discovered trusted peer: {device_name} at {ip_address}")
    
    if mesh_engine:
        mesh_engine.register_peer(ip_address)
        
        # print(f"🚀 Triggering secure sync handshake testing over TCP to {ip_address}...")
        # mock_sync_event = {
        #     "action": "PEER_CONNECTED",
        #     "file_name": "network_mesh",
        #     "timestamp": time.time()
        # }
        # mesh_engine.send_secure_payload(ip_address, mock_sync_event)

def on_local_file_changed(event):
    """
    Fires automatically whenever the file watcher detects a stable change.
    Ingests the complete watchdog event object, serializes the specific 
    action, and broadcasts the payload to connected peers.
    """
    app_settings = Settings()
    action = event.event_type.upper()
    
    # Calculate relative paths using the root directory to maintain folder structures
    src_name = os.path.relpath(event.src_path, app_settings.sync_path)
    dest_name = None
    
    if hasattr(event, 'dest_path') and event.dest_path:
        dest_name = os.path.relpath(event.dest_path, app_settings.sync_path)

    print(f"📡 File event caught: [{action}] {src_name}" + (f" -> {dest_name}" if dest_name else ""))
    
    # Bundle the distinct payload requirements via the serializer
    sync_payload = EventSerializer.serialize(
        action=action,
        src_name=src_name,
        dest_name=dest_name,
        sync_path=app_settings.sync_path
    )

    if mesh_engine:
        mesh_engine.broadcast_payload(sync_payload)

    # print(full_path)
    
    # if action in ("CREATED", "MODIFIED") and os.path.exists(full_path):
    #     print(full_path)
    #     try:
    #         with open(full_path, "rb") as f:
    #             raw_bytes = f.read()
    #             # Encode the raw binary to a safe ASCII text string for JSON transmission
    #             file_content_base64 = base64.b64encode(raw_bytes).decode('utf-8')
    #     except Exception as e:
    #         print(f"⚠️ Could not read file content for transmission: {e}")
    #         return

    # sync_payload = {
    #     "action": action,
    #     "file_name": file_name,
    #     "file_data": file_content_base64,
    #     "timestamp": time.time()
    # }

    # if mesh_engine:
    #     mesh_engine.broadcast_payload(sync_payload)

def on_remote_file_received(payload):
    """
    Fires automatically when the mesh network receives a secure sync instruction 
    from a remote peer. Writes the physical changes directly to disk.
    """
    action = payload["action"]
    app_settings = Settings()
    
    if action == "MOVED":
        src_name = payload["src_name"]
        dest_name = payload["dest_name"]
        full_src_path = os.path.join(app_settings.sync_path, src_name)
        full_dest_path = os.path.join(app_settings.sync_path, dest_name)
        
        print(f"🛠️  Applying remote changes locally: [MOVED] {src_name} -> {dest_name}")
        
        # Ensure target subfolder structure exists before renaming
        dest_dir = os.path.dirname(full_dest_path)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
            
        if os.path.exists(full_src_path):
            os.rename(full_src_path, full_dest_path)
            print(f"🚚 File moved locally: {full_dest_path}")
            
    elif action in ("CREATED", "MODIFIED"):
        file_name = payload["file_name"]
        full_path = os.path.join(app_settings.sync_path, file_name)
        
        print(f"🛠️  Applying remote changes locally: [{action}] -> {file_name}")
        
        # Ensure all multi-level parent subfolders exist on disk
        parent_dir = os.path.dirname(full_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        raw_bytes = base64.b64decode(payload["file_data"].encode('utf-8'))
        with open(full_path, "wb") as f:
            f.write(raw_bytes)
        print(f"💾 File synchronized and written to disk: {full_path}")
        
    elif action == "DELETED":
        file_name = payload["file_name"]
        full_path = os.path.join(app_settings.sync_path, file_name)
        
        print(f"🛠️  Applying remote changes locally: [DELETED] -> {file_name}")
        
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"🗑️ File deleted locally to match remote cluster.")
        
    # elif action == "DELETED":
    #     if os.path.exists(full_path):
    #         os.remove(full_path)
    #         print(f"🗑️ File deleted locally to match remote cluster.")

def main():
    global mesh_engine
    print("-----------------------------------------")
    print("           Sharron Full Stack Node       ")
    print("-----------------------------------------")
    
    app_settings = Settings()
    
    if not app_settings.is_onboarded():
        print("🔨 Initializing a fresh Sharron storage node...")
        app_settings.initialize_fresh_cluster()
    
    session_password = app_settings.get_raw_passphrase_for_session()
    
    crypto = CryptoEngine(session_password)
    mesh_engine = MeshNetwork(crypto, on_remote_file_received)
    
    mesh_engine.start_server()
    
    my_hostname = socket.gethostname()
    print(f"💻 Node Identity: [{my_hostname}]")
    
    discovery = DiscoveryMesh(my_hostname, crypto, on_peer_found)
    discovery.start()

    watcher = DirectoryWatcher(app_settings.sync_path, on_local_file_changed)
    watcher.start()
    
    print("\nPress Ctrl+C to stop the node runtime engine.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Sharron core layers safely...")
        discovery.stop()
        mesh_engine.stop()
        watcher.stop()

if __name__ == "__main__":
    main()
