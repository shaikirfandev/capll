# LIN Bus Protocol Guide
## LIN 2.2A | LDF Files | Master/Slave | CAPL & Python Testing

---

## 1. LIN Overview

**LIN (Local Interconnect Network)** is a low-cost, single-wire serial network:
- **Speed:** 1–20 kbit/s (typically 9.6 or 19.2 kbit/s)
- **Topology:** Single master, up to 16 slaves
- **Wire:** Single wire + ground (uses vehicle chassis)
- **Use cases:** Seat control, mirrors, sunroof, HVAC, switches, window lift

**Why not CAN?**
| Feature | CAN | LIN |
|---------|-----|-----|
| Cost | Higher | Lower (no transceiver IC) |
| Speed | 1 Mbit/s | 20 kbit/s |
| Wires | 2 (CANH/CANL) | 1 (single wire) |
| Nodes | 32+ | 16 max |
| Master | None (CSMA) | 1 master required |

---

## 2. LIN Frame Structure

A LIN frame has a **header** (from master) and a **response** (from slave or master):

```
[Break Field] [Sync Byte] [PID] [Data 0..N] [Checksum]
    13 bits      0x55       1B    1–8 bytes      1B
```

| Field | Description |
|-------|-------------|
| **Break** | At least 13 dominant bits — signals frame start |
| **Sync** | 0x55 — allows slave baud rate auto-detection |
| **PID** | Protected ID = Frame ID (6 bits) + 2 parity bits |
| **Data** | 1–8 bytes of payload |
| **Checksum** | Classic (LIN 1.x) or Enhanced (LIN 2.x, includes PID) |

### PID Calculation
```
ID bits [5:0] = Frame ID (0–63)
P0 = ID0 XOR ID1 XOR ID2 XOR ID4
P1 = NOT(ID1 XOR ID3 XOR ID4 XOR ID5)
PID = P1 P0 ID5 ID4 ID3 ID2 ID1 ID0
```

---

## 3. LIN Schedule Table

The master controls **when** each frame is sent using a schedule table:

```
Schedule "NormalSchedule":
  Frame 0x01 (Light_Cmd)   every 10ms
  Frame 0x02 (Mirror_Cmd)  every 20ms
  Frame 0x11 (Light_Sts)   every 10ms
  Frame 0x12 (Mirror_Sts)  every 20ms
  Frame 0x3C (Diag_Req)    on-demand
```

Master sends header at exact schedule time → slave responds within response space.

---

## 4. LDF (LIN Description File)

The LDF file describes the complete LIN cluster:

```ldf
LIN_description_file;
LIN_protocol_version = "2.2";
LIN_language_version = "2.2";
LIN_speed = 19.2 kbps;

Nodes {
  Master: GatewayECU, 5 ms, 0.1 ms;
  Slaves: SeatModule, MirrorModule;
}

Signals {
  SeatPosition: 8, 0, SeatModule, GatewayECU;
  ReclineAngle: 8, 0, SeatModule, GatewayECU;
  SeatCmd: 8, 0, GatewayECU, SeatModule;
}

Frames {
  SeatStatus: 0x11, SeatModule, 2 {
    SeatPosition, 0;
    ReclineAngle, 8;
  }
  SeatControl: 0x01, GatewayECU, 1 {
    SeatCmd, 0;
  }
}

Schedule_tables {
  NormalSchedule {
    SeatControl    delay 10 ms;
    SeatStatus     delay 10 ms;
  }
}
```

---

## 5. LIN Diagnostics (ISO 17987 / LIN 2.x)

LIN supports node diagnostics via frames 0x3C (master request) and 0x3D (slave response).

| Frame ID | Name | Direction |
|----------|------|-----------|
| 0x3C | Master request | Master → Slave |
| 0x3D | Slave response | Slave → Master |

Data format follows NAD (Node Address for Diagnostics), PCI, SID structure — similar to UDS/ISO 15765.

```
Master Request (0x3C):
[NAD] [PCI] [SID] [D1] [D2] [D3] [D4] [D5]

NAD:  0x01 = Slave 1 node address
PCI:  0x06 = 6 more bytes follow
SID:  0x22 = ReadDataByIdentifier (UDS service)
```

---

## 6. CAPL LIN Testing

```capl
variables {
  msTimer tLINMonitor;
  int g_SeatPos = 0;
  int g_ReclineAngle = 0;
}

on start {
  setTimer(tLINMonitor, 1000);
  write("LIN Monitor started");
}

/* Receive seat status frame from slave */
on linFrame 0x11 {
  g_SeatPos     = this.byte(0);
  g_ReclineAngle = this.byte(1);
  write("Seat Position: %d, Recline: %d", g_SeatPos, g_ReclineAngle);
}

/* Send seat control command */
on key 'f' {
  linFrame cmd;
  cmd.id = 0x01;
  cmd.dlc = 1;
  cmd.byte(0) = 0x05;  // Move forward
  output(cmd);
  write("Sent: Move seat forward");
}

on timer tLINMonitor {
  /* Check if slave is still responding */
  write("LIN Monitor: Seat=%d Recline=%d", g_SeatPos, g_ReclineAngle);
  setTimer(tLINMonitor, 1000);
}
```

---

## 7. Python LIN Simulation (python-lin / serial)

```python
import serial
import time

# LIN master via UART (no real HW) — conceptual demonstration
class LINMaster:
    def __init__(self, port, baud=19200):
        self.ser = serial.Serial(port, baud, timeout=0.05)

    def send_break(self):
        """Generate break field: set baud to 1/13 and send 0x00."""
        self.ser.baudrate = 1200  # Simulate break (13 bit-times at normal baud)
        self.ser.write(bytes([0x00]))
        self.ser.flush()
        self.ser.baudrate = 19200

    def compute_pid(self, frame_id):
        id_bits = frame_id & 0x3F
        p0 = ((id_bits >> 0) ^ (id_bits >> 1) ^ (id_bits >> 2) ^ (id_bits >> 4)) & 1
        p1 = (~((id_bits >> 1) ^ (id_bits >> 3) ^ (id_bits >> 4) ^ (id_bits >> 5))) & 1
        return id_bits | (p0 << 6) | (p1 << 7)

    def send_header(self, frame_id):
        self.send_break()
        pid = self.compute_pid(frame_id)
        self.ser.write(bytes([0x55, pid]))  # SYNC + PID

    def send_frame(self, frame_id, data: list):
        self.send_header(frame_id)
        checksum = (sum(data) + self.compute_pid(frame_id)) & 0xFF
        checksum = (~checksum) & 0xFF  # Enhanced checksum
        self.ser.write(bytes(data + [checksum]))

    def read_response(self, length):
        return self.ser.read(length + 1)  # data + checksum

    def close(self):
        self.ser.close()
```

---

## 8. LIN Error Types

| Error | Description |
|-------|-------------|
| **No Response** | Slave did not respond within response space |
| **Framing Error** | Stop bit missing |
| **Checksum Error** | Received checksum ≠ computed |
| **Parity Error** | PID parity bits incorrect |
| **Sync Error** | Could not sync to 0x55 byte |
| **Bit Error** | Sent bit ≠ monitored bus state |

---

## 9. Interview Q&A

**Q: Why is LIN a master-slave protocol with no collision detection?**
> LIN uses a single master that controls all frame scheduling. Only one node transmits response per frame slot (predetermined in LDF). This eliminates collisions entirely — no CSMA/CD needed. The simplicity significantly reduces cost (no complex transceiver, no arbitration logic).

**Q: What is the difference between classic and enhanced LIN checksum?**
> Classic checksum (LIN 1.x): sum of data bytes only, inverted. Enhanced checksum (LIN 2.x): sum of PID + all data bytes, inverted. Enhanced checksum provides better fault coverage since the PID is also protected.

**Q: How does a slave detect the baud rate automatically?**
> The sync byte (0x55) has a specific bit pattern (01010101) that allows the slave to measure the bit time by timing the falling and rising edges, then compute the baud rate.

**Q: When would you choose LIN over CAN for a subsystem?**
> LIN when: fewer than 16 nodes, low data rate acceptable (seat position, mirror angle), cost is critical (switches, simple actuators), single-wire installation is beneficial. CAN is preferred for safety-critical, high-speed, or multi-master communication needs.
