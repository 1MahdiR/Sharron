import socket
import time

from config.settings import Settings
from core.crypto import CryptoEngine
from core.discovery import DiscoveryMesh
from core.mesh import MeshNetwork
from core.watcher import DirectoryWatcher

mesh_engine = None

def on_peer_found(ip_address, device_name):
    """Fires automatically when a peer is discovered via UDP heartbeat."""
    print(f"\n✨ Discovered trusted peer: {device_name} at {ip_address}")
    
    if mesh_engine:
        mesh_engine.register_peer(ip_address)
        
        print(f"🚀 Triggering secure sync handshake testing over TCP to {ip_address}...")
        mock_sync_event = {
            "action": "PEER_CONNECTED",
            "file_name": "network_mesh",
            "timestamp": time.time()
        }
        mesh_engine.send_secure_payload(ip_address, mock_sync_event)

def on_local_file_changed(action, file_name):
    """
    Fires automatically whenever the file watcher detects a stable change.
    Packages the event and sends it to our active network mesh.
    """
    print(f"📡 File event caught: [{action}] {file_name}")
    print("   Broadcasting sync instructions to connected peers...")

    sync_payload = {
        "action": action,
        "file_name": file_name,
        "timestamp": time.time()
    }

    if mesh_engine:
        mesh_engine.broadcast_payload(sync_payload)

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
    mesh_engine = MeshNetwork(crypto)
    
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
