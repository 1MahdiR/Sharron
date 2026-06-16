import socket
import threading
import json
from core.crypto import CryptoEngine

TCP_PORT = 58888

class MeshNetwork:
    def __init__(self, crypto_engine: CryptoEngine):
        """
        Initializes the TCP Mesh Network.
        
        :param crypto_engine: Fully initialized CryptoEngine instance
        """
        self.crypto = crypto_engine
        self.server_socket = None
        self.running = False

        self.discovered_peers = set()

    def register_peer(self, peer_ip: str):
        """Adds a newly discovered peer IP address to the active routing tables."""
        if peer_ip not in self.discovered_peers:
            self.discovered_peers.add(peer_ip)
            print(f"🔗 Peer {peer_ip} registered in mesh network memory.")

    def start_server(self):
        """Spins up the permanent TCP listening server in a background thread."""
        self.running = True
        server_thread = threading.Thread(target=self._server_loop, daemon=True)
        server_thread.start()
        print(f"🔒 TCP Mesh Server listening securely on port {TCP_PORT}...")

    def stop(self):
        """Safely tears down the TCP server socket."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

    def _server_loop(self):
        """Accepts incoming peer connections and sends them to a handshake handler."""
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
        """Executes the challenge-response handshake before allowing data transmission."""
        peer_ip = addr[0]
        try:
            challenge = self.crypto.generate_challenge()
            sock.sendall(challenge.encode('utf-8'))

            encrypted_solution = sock.recv(1024).decode('utf-8')

            if not self.crypto.verify_challenge_solution(challenge, encrypted_solution):
                print(f"⚠️ [Security Warning] Handshake failed for {peer_ip}. Dropping connection.")
                sock.close()
                return

            print(f"✅ [Handshake Verified] Secure session established with {peer_ip}!")
            
            raw_encrypted_data = sock.recv(4096)
            if raw_encrypted_data:
                decrypted_bytes = self.crypto.decrypt_data(raw_encrypted_data)
                payload = json.loads(decrypted_bytes.decode('utf-8'))
                print(f"📥 [Received Payload] From {peer_ip}: {payload}")

        except Exception as e:
            print(f"⚠️ Connection error handling {peer_ip}: {e}")
        finally:
            sock.close()

    def send_secure_payload(self, target_ip: str, payload: dict) -> bool:
        """
        Connects to a remote peer, solves their security challenge, 
        and pushes an encrypted JSON message block.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0) # Prevent hanging forever if host is unreachable

        try:
            sock.connect((target_ip, TCP_PORT))

            challenge = sock.recv(1024).decode('utf-8')

            solution = self.crypto.solve_challenge(challenge)
            sock.sendall(solution.encode('utf-8'))

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
        """
        Iterates over all registered peer IP addresses and dispatches
        the secure payload to each target.
        """
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