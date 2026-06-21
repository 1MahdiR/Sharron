# 🚀 Sharron

Sharron is an experimental, local-first, peer-to-peer (P2P) file synchronization engine built entirely from scratch in Python. It allows machines on the same local network to securely discover each other, establish secure TCP tunnels, and automatically replicate directory changes without relying on a centralized cloud server.

> ⚠️ **Disclaimer:** This project is an ongoing architectural experiment and an MVP. It is intended for educational and exploration purposes, not for hosting production/critical data.

---

## 🏗️ How it Works under the Hood

Sharron is completely decentralized and operates using three distinct concurrent systems:

1. **UDP Discovery Mesh:** Every 3 seconds, nodes broadcast an encrypted cryptographic packet containing their identity onto the local subnet. Peers listening on the mesh decrypt this packet and dynamically assemble an in-memory routing table of trusted node IPs.
2. **Challenge-Response Security Handshake:** When a node pushes an update, it establishes a direct TCP socket connection with a peer. The peer issues a cryptographically random challenge (nonce) which the sender must solve using a pre-shared passphrase key. If authentication fails, the connection drops immediately.
3. **Reactive Filesystem Watcher:** Using native OS event listeners hook systems via `watchdog`, Sharron actively tracks file creations, modifications, moves, and deletions, serializing those events into encrypted JSON payload frames that stream across the network mesh.

---

## ✨ Features Already Built
* **True Peer-to-Peer Topology:** Zero central server dependencies.
* **Mutual Exclusion Blind Spot Protection:** Built-in timestamp validation filters to distinguish between real human edits and incoming disk sync operations, preventing infinite network feedback loops.
* **Fallback Self-Healing System:** If a node receives a file update payload with incomplete data (or a `MOVED` command for a source file it doesn't possess), it triggers an out-of-band `FILE_REQUEST` pull query to dynamically heal the missing target.
* **Large File Optimization:** Separates connection timeouts from data transmission windows to allow large transfers over local networks safely.

---

## 🛠️ Getting Started

### 1. Install Dependencies
Clone the repository and install the filesystem watching and cryptographic primatives:
```bash
git clone [https://github.com/YOUR_USERNAME/sharron.git](https://github.com/YOUR_USERNAME/sharron.git)
cd sharron
pip install -r requirements.txt
```

### 2. Run a Storage Node
Launch the node engine. On its first boot, Sharron will automatically configure your default sync path (SharronDrive) and register your local configuration:
```bash
python main.py
```

## 🗺️ Project Roadmap

Sharron is evolving from a purely reactive live-event engine into a persistent, state-aware mesh. Contributions, feature suggestions, and pull requests are welcome across any of these target horizons:

* **🗄️ Phase 1: Local State Tracking (Next Up)**
  Move away from pure real-time event memory by building a persistent file index (SQLite or JSON state maps). This index will track path hashes and timestamps to allow nodes to understand their own folder state across application restarts.

* **🧠 Phase 2: Metadata Manifest Exchange & Delta Sync**
  Implement a peer-to-peer manifest sync routine upon connection. Nodes will trade state maps to compute directory differences (diff lists), allowing them to automatically sync changes that occurred while a machine was offline.

* **⚔️ Phase 3: Conflict Resolution & Convergence**
  Introduce deterministic fork-handling policies to deal with simultaneous offline edits. If a file was modified on two nodes during a network split, the engine will automatically branch a `.conflict` copy instead of blindly overwriting bytes.

* **💻 Phase 4: Native UX Integration**
  Encapsulate the core Python engine within a lightweight system tray or background service daemon so that sync operations happen seamlessly without an open terminal window.