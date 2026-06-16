import socket
import time
from config.settings import Settings
from core.crypto import CryptoEngine
from core.discovery import DiscoveryMesh
from core.mesh import MeshNetwork

# Global reference to trigger sending payloads inside our discovery callback
mesh_engine = None

def on_peer_found(ip_address, device_name):
    """Fires automatically when a peer is discovered via UDP heartbeat."""
    print(f"\n✨ Discovered trusted peer: {device_name} at {ip_address}")
    
    print(f"🚀 Triggering secure sync handshake over TCP to {ip_address}...")
    mock_sync_event = {
        "action": "FILE_MODIFIED",
        "file": "budget.xlsx",
        "hash": "sha256_xyz789_placeholder"
    }
    
    mesh_engine.send_secure_payload(ip_address, mock_sync_event)

def main():
    global mesh_engine
    print("-----------------------------------------")
    print("           Sharron Full Stack Node       ")
    print("-----------------------------------------")

    app_settings = Settings()
    
    session_password = app_settings.get_raw_passphrase_for_session()
    
    crypto = CryptoEngine(session_password, app_settings.salt)
    mesh_engine = MeshNetwork(crypto)
    
    mesh_engine.start_server()
    
    my_hostname = socket.gethostname()
    print(f"💻 Node Identity: [{my_hostname}]")
    discovery = DiscoveryMesh(my_hostname, crypto, on_peer_found)
    discovery.start()
    
    print("\nPress Ctrl+C to stop the node runtime engine.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Sharron core layers safely...")
        discovery.stop()
        mesh_engine.stop()

if __name__ == "__main__":
    main()