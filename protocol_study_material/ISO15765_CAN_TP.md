# ISO 15765 – CAN Transport Protocol (CAN TP) Study Material
## The Backbone of UDS over CAN

---

## 1. What is ISO 15765?

**ISO 15765** (also known as **CAN TP** or **ISO-TP**) is the **ISO transport protocol for CAN bus** that enables transmission of messages exceeding the 8-byte CAN frame payload limit.

- Required because UDS (ISO 14229) messages can be much larger than 8 bytes (e.g., ReadDataByIdentifier responses, firmware flashing)
- Provides **segmentation, flow control, and reassembly**
- Operates between the CAN data link layer and the UDS application layer

**Standard parts:**
| Part | Content |
|---|---|
| ISO 15765-1 | General information |
| ISO 15765-2 | Specification and requirements (Transport layer) |
| ISO 15765-3 | Diagnostic communication manager for CAN (AUTOSAR) |
| ISO 15765-4 | Requirements for emission-related systems (OBD) |

---

## 2. Why CAN TP?

| Without CAN TP | With CAN TP |
|---|---|
| Max 8 bytes per message | Up to **4095 bytes** (classic) or **4GB** (CAN FD extended) |
| No segmentation support | Automatic segmentation and reassembly |
| No flow control | Built-in flow control (BS, STmin) |
| Application must handle all | Transparent to UDS application layer |

---

## 3. ISO 15765-2 Frame Types

### 3.1 Single Frame (SF) – PCI Type 0x0
Used when the entire message fits in one CAN frame (≤ 7 bytes for classic CAN).

```
Byte 0: [0000 | LLLL]   0=SF type, LLLL=data length (0–7)
Bytes 1–7: Data
```

**Example** (3-byte UDS request: 0x10 0x03):
```
[02] [10] [03] [00] [00] [00] [00] [00]
  ^    ^    ^
  SF   SID  SessionType
  L=2
```

---

### 3.2 First Frame (FF) – PCI Type 0x1
First segment of a multi-frame message.

```
Byte 0: [0001 | HHHH]   1=FF type, HHHH=high nibble of length
Byte 1: [LLLLLLLL]      Low byte of total data length
Bytes 2–7: First 6 bytes of data
```

**Extended (CAN FD / large data):**
```
Byte 0: [0001 0000]   = 0x10 with length field = 0
Byte 1: [00000000]    = 0x00
Bytes 2–5: 4-byte total length
Bytes 6–N: Data
```

**Example** (0x0014 = 20 bytes total):
```
[10] [14] [62] [F1] [90] [31] [47] [4A]
  ^    ^    ← first 6 bytes of UDS response →
  FF  len=20
```

---

### 3.3 Consecutive Frame (CF) – PCI Type 0x2
Subsequent segments after the First Frame.

```
Byte 0: [0010 | NNNN]   2=CF type, NNNN=sequence number (0–15, wraps)
Bytes 1–7: Next 7 bytes of data
```

Sequence number starts at **1** with the first CF after FF, increments to 15, then wraps to 0.

---

### 3.4 Flow Control (FC) – PCI Type 0x3
Sent by the **receiver** after a First Frame to control data flow.

```
Byte 0: [0011 | FS]     3=FC type, FS=Flow Status
Byte 1: [BS]            Block Size (0 = unlimited)
Byte 2: [STmin]         Separation Time minimum
Bytes 3–7: 0x00 (padding)
```

**Flow Status (FS) values:**
| FS | Value | Meaning |
|---|---|---|
| ContinueToSend (CTS) | 0x00 | Sender may proceed |
| Wait (WT) | 0x01 | Receiver not ready, wait for next FC |
| Overflow (OVFLW) | 0x02 | Buffer overflow, abort |

**Block Size (BS):**
- `0x00` = Send all remaining frames without waiting for FC
- `0x01–0xFF` = Send this many CFs, then wait for next FC

**STmin (Separation Time Minimum):**
| Range | Meaning |
|---|---|
| 0x00 | No minimum separation |
| 0x01–0x7F | 1–127 ms |
| 0xF1–0xF9 | 100–900 µs |

---

## 4. Full Multi-Frame Exchange

```
Sender (Tester)                    Receiver (ECU)
     |                                   |
     |--- FF (First Frame, 20 bytes) --> |
     |                                   |  [receives FF, prepares buffer]
     |<-- FC (ContinueToSend, BS=0) -----|
     |                                   |
     |--- CF SN=1 --------------------> |
     |--- CF SN=2 --------------------> |
     |--- CF SN=3 --------------------> |   [last segment, reassemble]
     |                                   |
     |<-- Response (Single Frame) -------|
```

If BS=2:
```
     |--- FF --------------------------> |
     |<-- FC (BS=2, STmin=10ms) ---------|
     |--- CF SN=1 --------------------> |
     |--- CF SN=2 --------------------> |
     |<-- FC (BS=2, STmin=10ms) ---------|  [after 2 CFs]
     |--- CF SN=3 --------------------> |
     ...
```

---

## 5. CAN TP Addressing Modes

### 5.1 Normal Addressing (11-bit CAN ID)
- **Physical**: One specific sender → one specific receiver
  - Request: `0x7E0` (Tester) → ECU responds on `0x7E8`
  - Pattern: ECU request ID + 8 = response ID
- **Functional**: Tester → all ECUs (broadcast)
  - Request ID: `0x7DF`

### 5.2 Extended Addressing
First data byte carries an address extension byte.
```
[ExtAddr] [PCI] [Data...]
```

### 5.3 Mixed Addressing
Used in **ISO 15765-3** (AUTOSAR) with address extension in first byte.

### 5.4 Normal Fixed Addressing (SAE J1939)
```
CAN ID encodes source and target addresses directly:
[Priority | Reserved | DP | PF | DA | SA]
```

---

## 6. CAN TP Timing Parameters

| Parameter | Name | Typical Value |
|---|---|---|
| N_As | Time for sender to transmit an SF or FF | ≤ 25 ms |
| N_Ar | Time for receiver to transmit FC | ≤ 25 ms |
| N_Bs | Time sender waits for FC after FF | ≤ 1000 ms |
| N_Br | Time receiver waits to send FC after FF | ≤ 0 ms |
| N_Cs | Time sender waits between CFs | ≥ STmin |
| N_Cr | Time receiver waits for next CF | ≤ 1000 ms |

---

## 7. CAPL Example – Manual CAN TP Implementation

```capl
variables
{
  message 0x7E0 tpRequest;
  byte    gBuffer[4095];
  int     gTotalLen    = 0;
  int     gReceivedLen = 0;
  int     gSNExpected  = 1;
}

// Example: Send 20-byte UDS message with CAN TP
void sendMultiFrame(byte data[], int len)
{
  // Send First Frame
  tpRequest.byte(0) = 0x10 | ((len >> 8) & 0x0F);
  tpRequest.byte(1) = len & 0xFF;
  tpRequest.byte(2) = data[0];
  tpRequest.byte(3) = data[1];
  tpRequest.byte(4) = data[2];
  tpRequest.byte(5) = data[3];
  tpRequest.byte(6) = data[4];
  tpRequest.byte(7) = data[5];
  output(tpRequest);
}

// Receive flow control then send consecutive frames
on message 0x7E8
{
  byte pciType = (this.byte(0) >> 4) & 0x0F;

  if (pciType == 0x3) // Flow Control
  {
    byte fs    = this.byte(0) & 0x0F;
    byte bs    = this.byte(1);
    byte stmin = this.byte(2);

    if (fs == 0x00) // CTS
      write("Flow Control: CTS, BS=%d, STmin=%d ms", bs, stmin);
    else if (fs == 0x01)
      write("Flow Control: WAIT");
    else if (fs == 0x02)
      write("Flow Control: OVERFLOW - abort");
  }
}
```

---

## 8. OBD-II and ISO 15765-4

ISO 15765-4 defines CAN TP usage for **emission-related OBD diagnostics**:

| Parameter | Value |
|---|---|
| CAN speed | 250 kbps or 500 kbps |
| Request ID | 0x7DF (functional) |
| Response IDs | 0x7E8–0x7EF |
| Addressing mode | Normal addressing |
| Padding | 0xCC padded to 8 bytes |

**OBD Services:**
- Mode 0x01: Current powertrain data
- Mode 0x02: Freeze frame data
- Mode 0x03: Emission DTCs
- Mode 0x04: Clear DTCs
- Mode 0x09: Vehicle info (VIN)

---

## 9. CAN FD and ISO 15765 Extended

With **CAN FD** (up to 64-byte payloads):
- DL in First Frame can use extended format (total length > 4095 bytes)
- Up to **4GB** of data per session (theoretical)
- CAN FD padding typically uses `0xCC`

| Classic CAN | CAN FD |
|---|---|
| Max payload: 8 bytes | Max payload: 64 bytes |
| Max TP message: 4095 bytes | Max TP message: 4 GB |
| CFs carry 7 bytes each | CFs can carry up to 63 bytes each |

---

## 10. Common Interview Questions

**Q1: What is the purpose of ISO 15765 CAN TP?**
> It provides segmentation and reassembly of messages larger than 8 bytes over CAN, including flow control to prevent receiver buffer overflow.

**Q2: What are the 4 frame types in CAN TP?**
> Single Frame (SF), First Frame (FF), Consecutive Frame (CF), Flow Control (FC).

**Q3: What does Block Size = 0 mean in a Flow Control frame?**
> The sender can transmit all remaining consecutive frames without waiting for another FC.

**Q4: What is STmin?**
> Separation Time Minimum — the minimum time the sender must wait between consecutive frames. Range: 0–127 ms, or 100–900 µs (0xF1–0xF9).

**Q5: What happens if N_Bs timer expires?**
> Sender has not received a Flow Control frame within 1000 ms after sending a First Frame. The session is aborted.

**Q6: What is the difference between physical and functional addressing?**
> Physical (e.g., 0x7E0) targets one specific ECU. Functional (0x7DF) broadcasts to all ECUs — ECUs that recognize the service respond.

**Q7: If a 25-byte message needs to be sent, how many CAN frames are needed?**
> 1 First Frame (6 bytes of data) + 3 Consecutive Frames (7 bytes each = 21 bytes) = **4 frames total** (6+7+7+5=25).
