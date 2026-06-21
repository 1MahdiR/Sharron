import socket
import threading
import json
from core.crypto import CryptoEngine

TCP_PORT = 58888

class MeshNetwork:
    def __init__(self, crypto_engine: CryptoEngine, remote_change_callback=None):
        self.crypto = crypto_engine
        self.server_socket = None
        self.running = False

        self.discovered_peers = set()

        self.remote_change_callback = remote_change_callback

    def register_peer(self, peer_ip: str):
        if peer_ip not in self.discovered_peers:
            self.discovered_peers.add(peer_ip)
            print(f"🔗 Peer {peer_ip} registered in mesh network memory.")

    def start_server(self):
        self.running = True
        server_thread = threading.Thread(target=self._server_loop, daemon=True)
        server_thread.start()
        print(f"🔒 TCP Mesh Server listening securely on port {TCP_PORT}...")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

    def _server_loop(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('', TCP_PORT))
            self.server_socket.listen(5)
        except Exception as e:
            print(f"❌ Failed to bind TCP server: {e}")
            return

        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                
                handler = threading.Thread(
                    target=self._handle_incoming_connection, 
                    args=(client_sock, addr), 
                    daemon=True
                )
                handler.start()
            except Exception:
                if not self.running:
                    break

    def _handle_incoming_connection(self, sock: socket.socket, addr: tuple):
        peer_ip = addr[0]
        try:
            sock.settimeout(5.0)

            challenge = self.crypto.generate_challenge()
            sock.sendall(challenge.encode('utf-8'))

            encrypted_solution = sock.recv(1024).decode('utf-8')

            if not self.crypto.verify_challenge_solution(challenge, encrypted_solution):
                print(f"⚠️ [Security Warning] Handshake failed for {peer_ip}. Dropping connection.")
                sock.close()
                return

            print(f"✅ [Handshake Verified] Secure session established with {peer_ip}!")

            sock.sendall(b"OK")

            sock.settimeout(300.0)
            
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break  # Sender is done transmitting everything!
                chunks.append(chunk)
                
            raw_encrypted_data = b"".join(chunks)
            
            if raw_encrypted_data:
                decrypted_bytes = self.crypto.decrypt_data(raw_encrypted_data)
                payload = json.loads(decrypted_bytes.decode('utf-8'))
                
                print(f"📥 [Received Payload] From {peer_ip}: [{payload['action']}] {payload['file_name']}")
                
                if self.remote_change_callback:
                    self.remote_change_callback(payload, peer_ip, self)

        except Exception as e:
            print(f"⚠️ Connection error handling {peer_ip}: {e}")
        finally:
            sock.close()

    def send_secure_payload(self, target_ip: str, payload: dict) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0) # Prevent hanging forever if host is unreachable

        try:
            sock.connect((target_ip, TCP_PORT))

            challenge = sock.recv(1024).decode('utf-8')

            solution = self.crypto.solve_challenge(challenge)
            sock.sendall(solution.encode('utf-8'))

            auth_confirmation = sock.recv(1024).decode('utf-8')
            if auth_confirmation != "OK":
                print(f"❌ Remote peer rejected authentication.")
                return False
            
            sock.settimeout(300.0)

            raw_bytes = json.dumps(payload).encode('utf-8')
            encrypted_payload = self.crypto.encrypt_data(raw_bytes)

            sock.sendall(encrypted_payload)
            return True

        except (socket.timeout, ConnectionRefusedError):
            print(f"❌ Destination {target_ip} unreachable. Peer is offline.")
            return False
        except Exception as e:
            print(f"⚠️ Failed to send payload to {target_ip}: {e}")
            return False
        finally:
            sock.close()

    def broadcast_payload(self, payload: dict):
        if not self.discovered_peers:
            print("📭 Broadcast skipped: No registered peers in routing memory.")
            return

        print(f"📡 Broadcasting payload to {len(self.discovered_peers)} registered peer(s)...")
        
        for peer_ip in list(self.discovered_peers):
            success = self.send_secure_payload(peer_ip, payload)
            if success:
                print(f"   ✅ Broadcast successfully delivered to {peer_ip}")
            else:
                print(f"   ❌ Broadcast delivery failed to {peer_ip}")