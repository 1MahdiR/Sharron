import socket
import time

from config.settings import Settings
from core.crypto import CryptoEngine
from core.discovery import DiscoveryMesh
from core.mesh import MeshNetwork
from core.watcher import DirectoryWatcher
from handlers.remote_events import on_remote_file_received
from handlers.local_events import LocalChangeHandler

class SharronNode:
    def __init__(self):
        self.settings = Settings()
        self.mesh_engine = None
        self.discovery = None
        self.watcher = None

    def on_peer_found(self, ip_address, device_name):
        print(f"\n✨ Discovered trusted peer: {device_name} at {ip_address}")
        if self.mesh_engine:
            self.mesh_engine.register_peer(ip_address)

    def bootstrap(self):
        print("-----------------------------------------")
        print("           Sharron Sync Engine           ")
        print("-----------------------------------------")
        
        if not self.settings.is_onboarded():
            print("🔨 Initializing a fresh Sharron storage node...")
            self.settings.initialize_fresh_cluster()
        
        session_password = self.settings.get_raw_passphrase_for_session()
        crypto = CryptoEngine(session_password)
        
        # Connect network layer to remote event handlers
        self.mesh_engine = MeshNetwork(crypto, on_remote_file_received)
        self.mesh_engine.start_server()
        
        node_identity = socket.gethostname()
        print(f"💻 Node Identity: [{node_identity}]")
        
        # Start Discovery Mesh
        self.discovery = DiscoveryMesh(node_identity, crypto, self.on_peer_found)
        self.discovery.start()

        # Connect local file changes to the broker handler
        local_handler = LocalChangeHandler(self.mesh_engine)
        self.watcher = DirectoryWatcher(self.settings.sync_path, local_handler.on_local_file_changed)
        self.watcher.start()
        
        print("\n🚀 Engine running. Press Ctrl+C to stop.")

    def shutdown(self):
        print("\n🛑 Shutting down Sharron core layers safely...")
        if self.discovery:
            self.discovery.stop()
        if self.watcher:
            self.watcher.stop()
        if self.mesh_engine:
            self.mesh_engine.stop()

def main():
    node = SharronNode()
    node.bootstrap()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.shutdown()

if __name__ == "__main__":
    main()