import socket
import time
import threading
from core.crypto import CryptoEngine

DISCOVERY_PORT = 59999
MAGIC_WORD = "SHARRON_PING"

class DiscoveryMesh:
    def __init__(self, hostname: str, crypto_engine: CryptoEngine, peer_discovered_callback):
        self.hostname = hostname
        self.crypto = crypto_engine
        self.peer_callback = peer_discovered_callback
        self.running = False

    def start(self):
        self.running = True

        listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listener_thread.start()
        
        broadcaster_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        broadcaster_thread.start()
        
        print("📡 Sharron Discovery Network Mesh is running...")

    def stop(self):
        self.running = False

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        payload_text = f"{MAGIC_WORD}-{self.hostname}"
        encrypted_payload = self.crypto.encrypt_data(payload_text.encode('utf-8'))

        while self.running:
            try:
                sock.sendto(encrypted_payload, ('255.255.255.255', DISCOVERY_PORT))
            except Exception as e:
                print(f"⚠️ Discovery Broadcast Error: {e}")
            time.sleep(3)
        sock.close()

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        sock.bind(('', DISCOVERY_PORT))

        while self.running:
            try:
                data, addr = sock.recvfrom(2048)
                
                try:
                    decrypted_bytes = self.crypto.decrypt_data(data)
                    message = decrypted_bytes.decode('utf-8')
                except Exception:
                    continue

                if message.startswith(MAGIC_WORD):
                    sender_hostname = '-'.join(message.split('-')[1:])
                    
                    if sender_hostname != self.hostname:
                        self.peer_callback(addr[0], sender_hostname)
                        
            except Exception as e:
                if self.running:
                    print(f"⚠️ Discovery Listener Error: {e}")
        sock.close()
