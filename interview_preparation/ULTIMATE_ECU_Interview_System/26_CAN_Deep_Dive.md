# CAN Deep Dive Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

CAN (Controller Area Network) remains the **dominant protocol in automotive** with over 90% of vehicles relying on it. A principal-level engineer must understand not just the protocol but the electrical layer, timing calculations, frame scheduling, DBC database design, error handling, and SocketCAN implementation.

**Key areas probed:**
- CAN 2.0A/B frame format in detail (every field)
- Bit timing, sample point, and oscillator tolerance
- CAN-FD dual bitrate and BRS bit mechanics
- CAN signal encoding (byte order, bit position, factor/offset)
- DBC file format and signal definition
- SocketCAN (Linux kernel CAN subsystem)
- ISO-TP (ISO 15765-2) for multi-frame messages
- CAN gateway — routing between buses
- Error frame analysis and fault isolation
- AUTOSAR COM layer signal extraction

---

## BEGINNER QUESTIONS

---

### Q1. Explain every field in a CAN 2.0A standard frame.

**Short Answer:** A CAN standard frame has 10 fields: SOF, Identifier, RTR, IDE, r0, DLC, Data, CRC, CRC Delimiter, ACK, ACK Delimiter, EOF, and IFS — totalling up to 111 bits.

**Detailed Expert Answer:**

```
CAN 2.0A Standard Frame (complete):

Bit position:  1   11    1  1  1   4    0-64     15   1   1   1  7   3
               ┌───┬─────┬──┬──┬──┬────┬─────────┬───┬───┬───┬──┬───┬───┐
               │SOF│ ID  │RTR│IDE│r0 │DLC│  Data  │CRC│CD │ACK│AD│EOF│IFS│
               └───┴─────┴──┴──┴──┴────┴─────────┴───┴───┴───┴──┴───┴───┘

Field explanations:

SOF (Start of Frame) — 1 bit, dominant (0)
  • Synchronises all receivers to the start of a new frame
  • Hard synchronisation occurs on SOF falling edge

ID — 11 bits (standard) or 29 bits (extended)
  • Message identifier AND priority (lower = higher priority)
  • ID 0x000 has highest priority on bus

RTR (Remote Transmission Request) — 1 bit
  • 0 (dominant) = data frame (contains actual data)
  • 1 (recessive) = remote frame (requests data from node with this ID)
  • Note: CAN-FD removed RTR (replaced with RRS bit, always 0)

IDE (Identifier Extension) — 1 bit
  • 0 (dominant) = standard frame (11-bit ID)
  • 1 (recessive) = extended frame (29-bit ID follows)
  • Also used for arbitration between std/ext frames with same 11-bit base

r0 (Reserved bit) — 1 bit
  • Always recessive in Classic CAN 2.0
  • In CAN-FD: this position is FDF (FD Frame) bit

DLC (Data Length Code) — 4 bits
  • Classic CAN: 0-8 (number of data bytes)
  • DLC 9-15 are treated as 8 in Classic CAN receivers
  • CAN-FD: DLC 9-15 map to 12,16,20,24,32,48,64 bytes

Data — 0 to 8 bytes (Classic) or 0 to 64 bytes (CAN-FD)
  • Transmitted MSBit first within each byte
  • Byte 0 is the first byte after DLC

CRC — 15 bits + 1 bit delimiter
  • Generator polynomial: x^15 + x^14 + x^10 + x^8 + x^7 + x^4 + x^3 + 1
  • Calculated over SOF + ID + RTR + IDE + r0 + DLC + Data
  • 1 bit CRC delimiter (recessive)

ACK — 1 bit + 1 bit delimiter
  • ACK slot: transmitter sends recessive; any receiver overwrites with dominant
  • If no receiver acknowledges → ACK error → transmitter detects no one heard it
  • ACK delimiter: always recessive (bit stuffing rule exception)

EOF (End Of Frame) — 7 recessive bits
  • Marks end of frame; no bit stuffing in EOF
  • Detecting a dominant bit here = form error

IFS (Intermission Field Spacing) — 3 recessive bits
  • Minimum gap between consecutive frames
  • Nodes move to IDLE or start next frame after IFS
```

**DBC signal encoding example:**
```
CAN ID 0x120, 8 bytes, contains vehicle speed signal:
  Signal name: VehicleSpeed
  Start bit: 16 (bit counting from Motorola: MSbit position)
  Length: 16 bits
  Byte order: Motorola (big-endian)
  Factor: 0.01
  Offset: 0
  Min: 0, Max: 327.67 km/h

Raw bytes: [0x12, 0x34, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00]
                   ↑─────↑
  Raw value = 0x1700 = 5888
  Physical = 5888 × 0.01 = 58.88 km/h
```

---

### Q2. How do you calculate CAN bit timing for 500 kbps on a 16 MHz oscillator?

**Short Answer:** Bit time = 1/bitrate. Divide into Time Quanta (Tq = prescaler/f_clk). Structure: Sync_Seg + Prop_Seg + Phase_Seg1 + Phase_Seg2 = total Tq per bit. Sample point is usually at 75-87.5% of bit time.

**Detailed Expert Answer:**

```
Given:
  Target bitrate = 500 kbps
  System clock   = 16 MHz

Step 1: Calculate target bit time
  Bit_time = 1 / 500,000 = 2 μs

Step 2: Choose prescaler (BRP) to get integer Tq count
  Tq = (BRP + 1) / f_clk = 2 / 16,000,000 = 125 ns  (BRP = 1)
  Tq per bit = Bit_time / Tq = 2000 ns / 125 ns = 16 Tq

Step 3: Allocate Tq segments
  Sync_Seg = 1 Tq (fixed by CAN standard)
  Remaining = 15 Tq

  Choose sample point at 87.5% = 14/16 Tq
  → Prop_Seg + Phase_Seg1 = 13 Tq (before sample point)
  → Phase_Seg2 = 2 Tq (after sample point)

  Practical allocation:
    Sync_Seg  = 1  (fixed)
    Prop_Seg  = 8  (propagation delay: max 2 × 150m × 5ns/m = 1.5 μs → 12 Tq max)
    Phase_Seg1 = 5
    Phase_Seg2 = 2
    Total     = 16 Tq ✓

  Sample point = (1 + 8 + 5) / 16 = 87.5% ✓

Step 4: Calculate SJW (Synchronisation Jump Width)
  SJW = min(4, Phase_Seg1, Phase_Seg2) = min(4, 5, 2) = 2 Tq

Register values (STM32 CAN_BTR):
  BRP  = 1   → Tq = 2×(1+1)/16MHz = wait, formula: Tq = (BRP+1)/f_clk
         Let's use BRP = 1: Tq = 2/16M = 125ns ✓
  TS1  = 12  (Prop + Phase1 = 13 Tq → TS1 register value = 13-1 = 12)
  TS2  = 1   (Phase2 = 2 Tq → TS2 register value = 2-1 = 1)
  SJW  = 1   (SJW = 2 Tq → SJW register value = 2-1 = 1)
```

**Why sample point matters:**
```
Sample point too early (e.g., 50%):
  → Less robust to propagation delay, bus glitches near end of bit
  → Common in CiA 601 recommendations for automotive: 75-80%

Sample point at 87.5%:
  → CiA 301 (CANopen) recommendation
  → More immune to ringing and bus reflections
  → Used in most passenger car applications

CAN-FD data phase: sample point often 70-75% (less forgiving, need tighter timing)
```

---

## INTERMEDIATE QUESTIONS

---

### Q3. How does ISO-TP (ISO 15765-2) work? Explain all frame types and flow control.

**Short Answer:** ISO-TP segments CAN messages longer than 8 bytes (Classic CAN) into multiple CAN frames. Four frame types: Single Frame (SF), First Frame (FF), Consecutive Frame (CF), and Flow Control (FC).

**Detailed Expert Answer:**

```
ISO-TP Frame Types:

1. Single Frame (SF) — message ≤ 7 bytes (Classic CAN)
   Byte 0: [0x0N] N = data length (1-7)
   Byte 1-N: Data
   
   Example: SF with 5 bytes
   [0x05][D0][D1][D2][D3][D4][pad][pad]

2. First Frame (FF) — message > 7 bytes, start
   Byte 0-1: [0x1L][LL] — L = 12-bit total length
   Byte 2-7: First 6 bytes of data
   
   Example: FF for 20-byte UDS response
   [0x10][0x14][D0][D1][D2][D3][D4][D5]
                ↑length=20

3. Consecutive Frame (CF)
   Byte 0: [0x2N] N = sequence number (1-F, wraps to 1)
   Byte 1-7: Up to 7 bytes of data
   
   CF 1: [0x21][D6][D7][D8][D9][DA][DB][DC]
   CF 2: [0x22][DD][DE][DF][pad][pad][pad][pad]

4. Flow Control (FC) — sent by receiver to control flow
   Byte 0: [0x3F] F = 0 (CTS), 1 (Wait), 2 (Overflow)
   Byte 1: Block Size (BS) — 0=send all, N=send N CFs before next FC
   Byte 2: Separation Time Minimum (STmin)
           0x00-0x7F: 0-127 ms
           0xF1-0xF9: 100-900 μs
```

**Complete multi-frame exchange:**
```
Tester → ECU: UDS 0x22 ReadDataByIdentifier (2 bytes)
  Single Frame: [0x03][0x22][0xF1][0x90] = [SF len=3][SID][DID high][DID low]

ECU → Tester: UDS 0x62 response with 20 bytes of VIN data
  First Frame:  [0x10][0x14][0x62][0xF1][0x90][W1][W2][W3]  (6 VIN bytes)
  
  Tester → ECU: Flow Control
  FC CTS:       [0x30][0x00][0x0A]
                      ↑BS=0  ↑STmin=10ms (send all, min 10ms between CFs)
  
  ECU → Tester: CF1: [0x21][W4][W5][W6][W7][W8][W9][WA]
  ECU → Tester: CF2: [0x22][WB][WC][WD][WE][WF][WG][WH] (last 2 bytes + padding)
  
  Complete! Tester reassembles: W1-WH = 17-byte VIN number
```

**SocketCAN ISO-TP implementation:**
```c
/* Linux kernel isotp module (AF_CAN, CAN_ISOTP) */
int isotp_init(const char *iface, uint32_t tx_id, uint32_t rx_id) {
    int fd = socket(AF_CAN, SOCK_DGRAM, CAN_ISOTP);
    
    struct sockaddr_can addr = {
        .can_family  = AF_CAN,
        .can_addr.tp = {
            .tx_id = tx_id,  /* ECU CAN request ID: 0x7DF or 0x7E0 */
            .rx_id = rx_id,  /* ECU CAN response ID: 0x7E8 */
        }
    };
    
    struct ifreq ifr;
    strncpy(ifr.ifr_name, iface, IFNAMSIZ - 1);
    ioctl(fd, SIOCGIFINDEX, &ifr);
    addr.can_ifindex = ifr.ifr_ifindex;
    
    /* Configure ISO-TP parameters */
    struct can_isotp_options opts = {
        .flags     = CAN_ISOTP_TX_PADDING | CAN_ISOTP_RX_PADDING,
        .frame_txtime = 10000,    /* 10ms between frames (STmin) */
        .ext_address  = 0,        /* No extended addressing */
        .txpad_content = 0xCC,    /* Padding byte */
        .rxpad_content = 0xCC,
    };
    setsockopt(fd, SOL_CAN_ISOTP, CAN_ISOTP_OPTS, &opts, sizeof(opts));
    
    bind(fd, (struct sockaddr*)&addr, sizeof(addr));
    return fd;
}
```

---

### Q4. How do you decode a CAN signal from raw bytes using DBC definition?

**Short Answer:** Extract bits according to start_bit, length, and byte_order (Intel/Motorola), then apply: physical_value = raw_value × factor + offset.

**Detailed Expert Answer:**

```c
/* CAN signal decoding — both Intel (little-endian) and Motorola (big-endian) */

typedef struct {
    const char *name;
    uint16_t start_bit;   /* DBC start bit */
    uint8_t  length;      /* Bit length */
    uint8_t  byte_order;  /* 0 = Intel (little-endian), 1 = Motorola */
    double   factor;
    double   offset;
} CANSignal_t;

/* Intel byte order (little-endian) — start_bit is LSBit position */
uint32_t decode_intel(const uint8_t *data, uint16_t start_bit, uint8_t len) {
    uint64_t raw = 0;
    memcpy(&raw, data, 8);  /* Load 8 bytes as 64-bit little-endian */
    raw >>= start_bit;
    raw &= (1ULL << len) - 1;
    return (uint32_t)raw;
}

/* Motorola byte order (big-endian) — start_bit is MSBit position */
uint32_t decode_motorola(const uint8_t *data, uint16_t start_bit, uint8_t len) {
    /* Convert Motorola start_bit (MSBit) to sequential bit stream */
    uint32_t result = 0;
    int bit_pos = (int)start_bit;
    
    for (int i = len - 1; i >= 0; i--) {
        int byte_n = bit_pos / 8;
        int bit_n  = 7 - (bit_pos % 8);  /* Motorola: bit 7 is MSBit of byte */
        if ((data[byte_n] >> bit_n) & 1) result |= (1U << i);
        
        /* Advance to next bit in Motorola layout */
        if ((bit_pos % 8) == 0) {
            bit_pos += 15;  /* Move to next byte's MSBit side */
        } else {
            bit_pos--;
        }
    }
    return result;
}

/* Decode a CAN signal to physical value */
double decode_signal(const uint8_t *can_data, const CANSignal_t *sig) {
    uint32_t raw;
    if (sig->byte_order == 0) {  /* Intel */
        raw = decode_intel(can_data, sig->start_bit, sig->length);
    } else {                      /* Motorola */
        raw = decode_motorola(can_data, sig->start_bit, sig->length);
    }
    return (double)raw * sig->factor + sig->offset;
}

/* Example usage */
void test_decode(void) {
    uint8_t can_data[8] = {0x00, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    
    CANSignal_t speed_sig = {
        .name       = "VehicleSpeed",
        .start_bit  = 8,     /* Intel: start at bit 8 = byte 1 bit 0 (LSBit) */
        .length     = 16,
        .byte_order = 0,     /* Intel */
        .factor     = 0.01,
        .offset     = 0.0,
    };
    
    double speed = decode_signal(can_data, &speed_sig);
    /* raw = 0x1700 = 5888, physical = 5888 × 0.01 = 58.88 km/h */
    printf("Speed: %.2f km/h\n", speed);
}
```

---

## ADVANCED QUESTIONS

---

### Q5. Explain SocketCAN architecture in Linux. How do you send and receive raw CAN frames?

**Detailed Expert Answer:**
```
SocketCAN kernel architecture:
                                                    
 User Space       │  Kernel Space                  
                  │                                
 Application      │  ┌──────────────────────────┐ 
 (socket API)     │  │    PF_CAN socket layer   │ 
        │         │  │  (af_can.c)               │ 
        │ syscall │  └──────────┬───────────────┘ 
        ▼         │             │                  
 ┌──────────────┐ │  ┌──────────▼───────────────┐ 
 │ socket()     │ │  │  CAN Protocol Family     │ 
 │ bind()       │ │  │  CAN_RAW / CAN_BCM /     │ 
 │ setsockopt() │ │  │  CAN_ISOTP / CAN_J1939   │ 
 │ read/write() │ │  └──────────┬───────────────┘ 
 └──────────────┘ │             │                  
                  │  ┌──────────▼───────────────┐ 
                  │  │  Network Device Layer    │ 
                  │  │  (vcan0, can0, can1...)  │ 
                  │  └──────────┬───────────────┘ 
                  │             │                  
                  │  ┌──────────▼───────────────┐ 
                  │  │  CAN Driver              │ 
                  │  │  (mcp251x, peak_usb,     │ 
                  │  │   flexcan, SocketCAN VCI)│ 
                  │  └──────────────────────────┘ 
```

**Complete raw CAN Tx/Rx example:**
```c
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>

int can_open(const char *iface) {
    int fd = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    
    struct ifreq ifr;
    strncpy(ifr.ifr_name, iface, IFNAMSIZ - 1);
    ioctl(fd, SIOCGIFINDEX, &ifr);
    
    struct sockaddr_can addr = {
        .can_family  = AF_CAN,
        .can_ifindex = ifr.ifr_ifindex,
    };
    bind(fd, (struct sockaddr*)&addr, sizeof(addr));
    return fd;
}

/* Send a raw CAN frame */
int can_send(int fd, uint32_t can_id, const uint8_t *data, uint8_t dlc) {
    struct can_frame frame = {
        .can_id  = can_id,
        .can_dlc = dlc,
    };
    memcpy(frame.data, data, dlc);
    return (int)write(fd, &frame, sizeof(frame));
}

/* Send CAN-FD frame */
int canfd_send(int fd, uint32_t can_id, const uint8_t *data, uint8_t len) {
    /* Enable CAN-FD on socket */
    int enable_canfd = 1;
    setsockopt(fd, SOL_CAN_RAW, CAN_RAW_FD_FRAMES, &enable_canfd, sizeof(enable_canfd));
    
    struct canfd_frame frame = {
        .can_id = can_id | CANFD_BRS,  /* Enable bit rate switch */
        .flags  = CANFD_BRS,
        .len    = len,
    };
    memcpy(frame.data, data, len);
    return (int)write(fd, &frame, sizeof(frame));
}

/* Receive with hardware timestamp */
int can_recv_ts(int fd, struct can_frame *frame, struct timeval *ts) {
    /* Enable hardware timestamps */
    int enable = SOF_TIMESTAMPING_RX_HARDWARE;
    setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &enable, sizeof(enable));
    
    char buf[sizeof(struct can_frame) + 64];  /* Space for cmsg */
    struct msghdr msg = {.msg_control = buf, .msg_controllen = sizeof(buf)};
    struct iovec iov = {.iov_base = frame, .iov_len = sizeof(*frame)};
    msg.msg_iov = &iov;
    msg.msg_iovlen = 1;
    
    recvmsg(fd, &msg, 0);
    
    /* Extract timestamp from control message */
    for (struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg); cmsg;
         cmsg = CMSG_NXTHDR(&msg, cmsg)) {
        if (cmsg->cmsg_level == SOL_SOCKET &&
            cmsg->cmsg_type  == SO_TIMESTAMPING) {
            struct timespec *tspec = (struct timespec*)CMSG_DATA(cmsg);
            ts->tv_sec  = tspec[2].tv_sec;
            ts->tv_usec = tspec[2].tv_nsec / 1000;
        }
    }
    return 0;
}
```

**CAN filter (receive only specific IDs):**
```c
void can_set_filter(int fd, uint32_t id, uint32_t mask) {
    struct can_filter filter = {
        .can_id   = id,    /* Only receive frames matching id & mask */
        .can_mask = mask,
    };
    /* Example: receive only 0x18FF0000-0x18FF00FF (J1939 PGN 0xFF00) */
    setsockopt(fd, SOL_CAN_RAW, CAN_RAW_FILTER, &filter, sizeof(filter));
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q6. You are debugging a CAN bus where a DTC is being set "CAN timeout" on a specific ECU. The ECU vendor says their ECU is fine. How do you find the truth?

**Expert Answer:**

"This is a common integration problem. 'CAN timeout' DTC means an ECU expected a message and didn't receive it within its supervision window.

**Step 1 — Identify exact supervision parameters:**
```
Ask ECU vendor for their ComM/COM configuration:
  Message ID expected: 0x120 (VehicleSpeed)
  Supervision period: 20ms
  Timeout factor: 3 (set DTC if 3 consecutive periods missed)
  Total timeout: 60ms
```

**Step 2 — Set up precise measurement:**
```
CANoe trace with CAPL trigger script:
variables {
    msTimer timeout_timer;
    int last_rx_120 = 0;
    int gap_max = 0;
}

on message 0x120 {
    int gap = timeNow() - last_rx_120;
    if (gap > gap_max) {
        gap_max = gap;
        write("Max gap for 0x120: %d ms", gap / 10);  /* timeNow in 100μs */
    }
    last_rx_120 = timeNow();
}
```

**Step 3 — Common root causes:**
```
1. BUS LOAD ISSUE: 0x120 is being delayed in transmission queue
   → Check bus load: if >70%, arbitration delay causes message to miss window
   → Solution: increase priority (lower CAN ID) for critical messages

2. SENDER TASK OVERRUN: ECU sending 0x120 has task jitter
   → Task should run every 10ms, but spikes to 25ms under load
   → Measure with logic analyser: actual period vs nominal

3. ECU CLOCK DRIFT: Sending ECU at 9.8ms cycle, receiving ECU at 10.0ms
   → After 6 cycles: accumulated 12ms drift
   → Supervision timer = 30ms → triggered! (30 - 6×1.96ms margin = used up)

4. GATEWAY DELAY: Messages passing through a gateway ECU
   → Gateway adds 5-10ms routing delay
   → Source ECU sends at 10ms, but arrives at dest at 12-15ms
```

**Step 4 — Resolution for bus load issue:**
```
Frame scheduling optimisation:
  Critical frames (safety): 0x001-0x0FF, < 5 ms cycle
  Powertrain frames: 0x100-0x2FF, 10-20 ms cycle
  Body frames: 0x300-0x5FF, 50-100 ms cycle
  Diagnostic frames: 0x600-0x7FF, event-based
```

**Production Insight:** At a KPIT vehicle integration project, this exact issue occurred with a transmission ECU claiming 'Engine speed timeout'. Root cause: the engine ECU was on a different CAN bus and a gateway was routing the signal. The gateway had a 15ms routing delay but the transmission ECU had a 20ms timeout window. Under worst-case scheduling, the message arrived at 18ms — just within 20ms. When engine compartment temperature rose, the gateway MCU ran slower and the routing delay increased to 22ms — exceeding the timeout. Fix: increase timeout from 20ms to 30ms AND reduce gateway routing priority."

---

## CHEAT SHEET — CAN Deep Dive

```
CAN 2.0A: 11-bit ID, max 8B data, up to 1 Mbps
CAN 2.0B: 29-bit ID, max 8B data, up to 1 Mbps
CAN-FD:   11/29-bit ID, max 64B data, up to 8 Mbps data phase

Frame fields:
  SOF → ID → RTR/RRS → IDE → r0/FDF → DLC → Data → CRC → ACK → EOF

Arbitration: Dominant (0) wins. Lower CAN ID = higher priority.
Bit stuffing: After 5 same bits → insert complement bit (removed by receiver)

Bit timing formula:
  Tq = (BRP + 1) / f_clk
  Bit_time = (1 + TS1 + TS2) × Tq
  Sample_point = (1 + TS1) / (1 + TS1 + TS2)
  Recommendation: 75-87.5% sample point

ISO-TP frames:
  SF: [0x0N] N=length, up to 7 bytes
  FF: [0x1H][LL] + 6 bytes, H+LL = total length
  CF: [0x2N] N=sequence 1-F, up to 7 bytes
  FC: [0x30/31/32][BS][STmin]

Signal decoding:
  Physical = raw × factor + offset
  Intel (little-endian): start_bit = LSBit position
  Motorola (big-endian): start_bit = MSBit position

SocketCAN key headers:
  #include <linux/can.h>
  #include <linux/can/raw.h>
  socket(PF_CAN, SOCK_RAW, CAN_RAW) → bind() → read/write()

Error states:
  TEC < 128:   Error Active (dominant error frames)
  TEC ≥ 128:   Error Passive (recessive error frames)
  TEC ≥ 256:   Bus-Off (disconnected)
```
