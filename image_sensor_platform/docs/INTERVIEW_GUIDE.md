# Embedded Firmware & Image Sensor Interview Guide
### 500+ Questions with Detailed Answers — Sony · Intel · NVIDIA · Qualcomm · Basler · FLIR · Bosch · OmniVision · TI

---

# PART 1 — Embedded Firmware (150 Questions)

## 1.1 Fundamentals

**Q1: What is the difference between volatile and const volatile in embedded C?**

`volatile` tells the compiler not to optimise away reads/writes to a variable because it can change outside normal program flow (hardware registers, ISR, DMA). `const volatile` means the variable is read-only by software but can change from outside — used for hardware status registers that the software reads but never writes.

```c
volatile uint32_t *UART_SR = (volatile uint32_t *)0x40011000;  // Status reg
const volatile uint32_t *DMA_STATUS = (const volatile uint32_t *)0x40026000;
```

---

**Q2: Why must DMA buffer addresses be cache-aligned and the cache be managed explicitly?**

Modern SoC caches operate at cache-line granularity (typically 32–64 bytes). If a DMA buffer straddles a cache line with other data, a cache clean/invalidate operation will corrupt that adjacent data. Moreover, if the CPU has written data to a buffer and the cache is dirty, the DMA will read stale data from RAM unless you explicitly call a cache-clean (`dcache_clean`) before starting the DMA write transfer. After a DMA-to-RAM (peripheral→memory) transfer completes, you must call `dcache_invalidate` so the CPU reads the DMA-written data rather than the stale cached copy.

**Rule of thumb:**
- Before P→M DMA: `dcache_invalidate(buffer, size)` → DMA writes → CPU reads new data.
- Before M→P DMA: `dcache_clean(buffer, size)` → CPU's data is in RAM → DMA reads it.

---

**Q3: Explain memory barriers (DMB, DSB, ISB) on ARM Cortex-M.**

- `DMB` (Data Memory Barrier): Ensures all explicit memory accesses before the DMB are visible before any explicit accesses after it. Use when ordering memory accesses between CPU and DMA/peripheral.
- `DSB` (Data Synchronization Barrier): Like DMB but also waits until all pending memory transactions complete. Required before changing MPU settings, before powering down, or before enabling/disabling interrupts that have memory effects.
- `ISB` (Instruction Synchronization Barrier): Flushes the instruction pipeline. Required after changing the vector table base register, after enabling the cache, or after modifying code in RAM.

---

**Q4: What is a race condition and how do you prevent it in a shared ISR/task buffer?**

A race condition occurs when two execution contexts (ISR and task, or two tasks) access shared data without synchronisation, producing different results depending on scheduling order.

Prevention strategies:
1. **Disable interrupts** around the critical section (bare-metal, single-core).
2. **Spinlock or mutex** (RTOS multi-task).
3. **Lock-free SPSC queue** (single-producer ISR, single-consumer task) — no locks needed if properly implemented with acquire/release memory ordering.
4. **Double-buffer** — ISR writes to ping, task reads from pong, atomic pointer swap.

---

**Q5: How does the ARM NVIC prioritise interrupts and what is priority inversion?**

The NVIC (Nested Vectored Interrupt Controller) uses numeric priority levels where lower numerical value = higher priority. Priority grouping (set via PRIGROUP in SCB→AIRCR) divides the priority bits into preemption priority and sub-priority.

Priority inversion: A high-priority task is blocked because it waits for a resource held by a low-priority task, and a medium-priority task preempts the low-priority task indefinitely. Resolution: Priority ceiling protocol or priority inheritance mutex (available in FreeRTOS via mutex — not binary semaphore).

---

**Q6: What is the difference between a semaphore and a mutex in RTOS?**

| | Mutex | Semaphore |
|---|---|---|
| Ownership | Has owner (only creator can release) | No owner |
| Priority inheritance | Yes (in FreeRTOS mutexes) | No |
| Use case | Mutual exclusion of shared resource | Signalling between tasks/ISRs |
| ISR safe | NO — cannot be given from ISR | YES — can post from ISR |
| Count | Binary (0 or 1) | Binary or counting |

---

**Q7: Explain the startup sequence of an STM32 from power-on to main().**

1. Power-on reset: program counter loads from vector table offset 0x00000004 (Reset_Handler).
2. Reset_Handler (startup_stm32xxx.s): copies `.data` section from Flash to RAM, zeroes `.bss`, optionally initialises the FPU.
3. SystemInit(): configures system clock (PLL setup), flash latency, MPU.
4. C++ static constructors called (if C++).
5. main() is called.

---

**Q8: What is the difference between little-endian and big-endian? Why does it matter for sensor register access?**

Little-endian: LSB at the lowest address (all ARM Cortex-M cores).
Big-endian: MSB at the lowest address (many network protocols, some sensor registers).

Sony IMX477 registers use big-endian for multi-byte values. Writing a 16-bit register value requires byte-swapping on a little-endian MCU:
```c
void i2c_write16_be(uint16_t reg, uint16_t val) {
    uint8_t buf[2] = { (uint8_t)(val >> 8), (uint8_t)(val & 0xFF) };
    i2c_write(reg, buf, 2);
}
```

---

**Q9: How do you detect and recover from a stuck I2C bus?**

Symptoms: SDA line is stuck low. Root cause: sensor was in the middle of a byte transfer when a reset occurred; its shift register holds a 0 bit, so it continues to hold SDA low.

Recovery procedure:
1. Toggle SCL nine times (enough to clock out any stuck byte).
2. After 9 clocks, SDA should have been released by the device.
3. Send a START followed by STOP condition.
4. Re-initialise the I2C peripheral.

The `hal_i2c_recover_bus()` function in this platform implements this procedure.

---

**Q10: What causes FIFO overflow in a MIPI CSI-2 receiver?**

1. System bus bandwidth insufficient: too many DMA channels competing.
2. DMA not starting fast enough after SOF — D-PHY FIFO fills up.
3. Memory latency too high (SDRAM refresh causing stall).
4. FIFO depth not programmed correctly for the data rate.

Mitigation: Use scatter-gather DMA, prioritise CSI-2 DMA channel highest, use SRAM buffer for first few lines, ensure FIFO interrupt fires before half-full.

---

## 1.2 MIPI CSI-2 and Image Interfaces

**Q11: Explain the CSI-2 packet structure.**

A long packet consists of:
- Short Packet Header: [Data Type:6 | Virtual Channel:2 | Word Count L:8 | Word Count H:8 | ECC:8]
- Payload: [Data bytes (Word Count bytes)]
- Footer: [CRC:16]

A short packet (Frame Start, Frame End, Line Start, Line End) is 4 bytes with no payload.

---

**Q12: What is ECC in MIPI CSI-2 and what can it detect/correct?**

ECC (Error Correction Code) is a Hamming code applied to the packet header. It can:
- **Detect and correct** 1-bit errors in the header (single-bit correction).
- **Detect** 2-bit errors in the header (double-bit detection, no correction).

ECC does NOT protect the payload — that is protected by the 16-bit CRC in the long packet footer.

---

**Q13: What is D-PHY HS-SETTLE time and how do you calculate it?**

HS-SETTLE is the time the receiver waits after detecting the SOT (Start Of Transmission) leader before sampling data. Too short: data is sampled before it's stable (bit errors). Too long: valid data is missed.

Calculation from MIPI spec:
```
T_HS-SETTLE = (85 + 6 × UI) + 300 ps
UI = 1 / (2 × lane_data_rate)
```
For 1500 Mbps per lane: UI = 667 ps
T_HS-SETTLE = 85 + 6 × 0.667 + 0.300 = 89.3 ns minimum

The `csi2_set_settle_time_ns()` function applies this value to the D-PHY timing registers.

---

**Q14: How do you validate that a CSI-2 receiver is receiving correct data?**

1. Enable sensor test pattern (e.g., color bars).
2. Capture frames and decode pixel data.
3. Compare decoded pixels to expected test pattern values.
4. Monitor ECC and CRC error counters — should be zero.
5. Verify frame dimensions match configured resolution.
6. Check SOF/EOF timestamps are correct.
7. Measure actual data rate using a protocol analyser or logic analyser with CSI-2 decoding.

---

**Q15: What is Virtual Channel in MIPI CSI-2?**

Virtual Channel (VC0–VC3) is a 2-bit field in every CSI-2 packet header that multiplexes up to 4 independent data streams over a single physical CSI-2 link. Common uses:
- Multi-sensor systems with a shared CSI-2 bus
- HDR: short and long exposure frames on VC0 and VC1
- Embedded data on VC1, image data on VC0

---

## 1.3 Sensor Driver Development

**Q16: What is the purpose of a register table in sensor initialisation?**

Sensor manufacturers provide a binary register table (sequence of {address, value} pairs) that configures hundreds of internal sensor parameters: PLL settings, clock distribution, MIPI configuration, readout mode, gain paths, ADC settings, black level calibration. The table is opaque — attempting to understand every register is unnecessary; the important parameters (gain, exposure, output size) are documented separately.

---

**Q17: How do you implement AEC (Auto Exposure Control)?**

AEC is typically done by the ISP (Image Signal Processor) on a SoC. On a bare-metal MCU platform, you implement a simple algorithm:

```
loop every N frames:
    current_luma = calculate_mean_luminance(frame)
    if abs(current_luma - target_luma) > tolerance:
        error = target_luma - current_luma
        new_exposure = current_exposure * (1 + Kp * error / target_luma)
        new_exposure = clamp(new_exposure, min_exp, max_exp)
        sensor_set_exposure(new_exposure)
        # Also adjust gain if at exposure limit
```

---

**Q18: What is the Sony Group Hold mechanism?**

Group hold (register 0x0104 on IMX477) is used for atomic updates of multiple sensor parameters. When bit 0 is set (group hold start), all register writes are buffered and applied simultaneously at the next frame boundary. This prevents tearing — the sensor switching gain mid-frame while keeping the old exposure.

Always use group hold when updating gain and exposure together.

---

**Q19: How does a dual-conversion gain work in CMOS sensors?**

Dual Conversion Gain (DCG) sensors have two charge-to-voltage conversion capacitances. High Conversion Gain (HCG) mode: small capacitance → high voltage per electron → low read noise, good for low light. Low Conversion Gain (LCG) mode: large capacitance → lower voltage per electron → handles higher photon counts before saturation.

DCG is activated by a register bit. Some sensors can capture both HCG and LCG in the same frame readout for HDR (each row alternates between the two gains).

---

**Q20: What is lens shading correction and how is it applied in firmware?**

Lens shading (also called vignetting) is the brightness falloff from centre to corners of the image due to the optical path. Correction: a 2D lookup table (LUT) of gain multipliers is loaded from EEPROM (calibrated per-lens). The ISP multiplies each pixel by its LUT coefficient. In firmware, calibration loading is triggered during sensor initialisation via `sensor_read_eeprom()`.

---

## 1.4 Real-Time Operating Systems (50 Questions abbreviated)

**Q51: Compare FreeRTOS task scheduling models.**

| Model | Mechanism | Use case |
|---|---|---|
| Preemptive | Higher-priority task immediately preempts | Real-time camera frame processing |
| Cooperative | Task yields CPU explicitly | Simple state machines |
| Time-slice | Equal-priority tasks share CPU time | Background logging |

FreeRTOS uses preemptive priority-based scheduling with optional round-robin for equal-priority tasks (configUSE_TIME_SLICING).

---

**Q52: What is stack overflow in RTOS and how do you detect it?**

Stack overflow: a task writes beyond its allocated stack space, corrupting adjacent memory. FreeRTOS detection:
1. **Stack canary**: a known pattern is written at the bottom of the stack; checked in the tick hook.
2. **MPU guard region**: MPU generates a fault on access to the guard page below the stack.
3. `uxTaskGetStackHighWaterMark()`: returns the minimum free stack words since task creation.

Always call `uxTaskGetStackHighWaterMark()` during integration and add 20% safety margin.

---

**Q53: When would you choose a message queue over a semaphore for inter-task communication?**

Use a queue when you need to pass data between tasks (not just signal). Example: streaming engine worker reads `csi2_frame_buffer_t*` pointers from a queue. The ISR puts a pointer into the queue (from ISR = xQueueSendFromISR). The worker receives it and processes the frame. A semaphore would only signal "a frame is available" — the worker would still need a shared variable for the actual pointer, introducing a race condition.

---

**Q54: How do you achieve deterministic real-time behavior with FreeRTOS?**

1. Assign distinct priorities — never share priorities between deadline-critical tasks.
2. Avoid malloc/free in tasks — use static allocation or memory pools.
3. Never call blocking functions in ISRs.
4. Keep ISRs extremely short — defer work to a high-priority task via queue.
5. Disable CPU caches or ensure cache coherency for shared DMA buffers.
6. Measure worst-case execution time with profiling before deployment.

---

**Q55: Explain the FreeRTOS tick interrupt and how it affects latency.**

The FreeRTOS tick (typically 1000 Hz = 1 ms period) drives the scheduler. A task waiting for a timeout is woken at the next tick. This means minimum timer resolution is 1 tick = 1 ms. For sub-millisecond precision (e.g., sensor trigger timing), use hardware timers directly, not FreeRTOS delays.

---

## 1.5 Linux Driver Development (50 Questions abbreviated)

**Q101: What is the V4L2 sub-device model?**

V4L2 (Video for Linux 2) uses a pipeline model: source devices (camera sensors) are modelled as sub-devices (v4l2_subdev). A bridge driver (CSI-2 receiver, ISP) connects to sub-devices via the Media Controller API. The pipeline is configured using `media-ctl` before streaming. This separation allows mixing and matching sensor drivers with different CSI-2 bridge drivers.

---

**Q102: What is V4L2 async sub-device registration?**

In DT-based systems, sensor and bridge drivers probe independently. The sensor driver registers itself with `v4l2_async_register_subdev()`. The bridge driver calls `v4l2_async_nf_register()` with a list of endpoints it expects. When all expected sub-devices are available, the notifier callback `bound()` and `complete()` are called, allowing the pipeline to be fully configured.

---

**Q103: How does runtime PM work in a camera sensor driver?**

The driver implements `pm_runtime_resume` (= `power_on`) and `pm_runtime_suspend` (= `power_off`). When streaming starts, `pm_runtime_get_sync()` bumps the reference count and calls power_on if the device is suspended. When streaming stops, `pm_runtime_put()` decrements the count; if it reaches zero after the autosuspend delay, power_off is called. This saves power when the camera is not streaming.

---

**Q104: What is the MEDIA_BUS_FMT for RAW12 Bayer and why does it matter?**

`MEDIA_BUS_FMT_SRGGB12_1X12` represents 12-bit RAW data in RGGB Bayer pattern on a 12-bit bus. The format code encodes: colour filter pattern (RGGB/GBRG/etc.), bit depth (8/10/12/16), and bit packing (1×12 = each pixel occupies exactly 12 bits on the bus with no padding). The ISP uses this code to select the correct demosaicing algorithm and data path.

---

**Q105: Explain DMA-BUF and why it is used for zero-copy video pipelines.**

DMA-BUF is a kernel framework for sharing DMA-capable memory buffers between different device drivers without copying. The camera sensor DMA fills a buffer. The ISP processes it without copying. The display engine DMA-maps the same buffer to display it. The user-space application maps it for computer vision. A file descriptor represents the buffer. This is how V4L2 DMABUF queue type works.

---

## 1.6 FPGA Interface (40 Questions abbreviated)

**Q141: What is the difference between synchronous and asynchronous FIFO in FPGA?**

Synchronous FIFO: single clock domain for both read and write. Used when producer and consumer share the same clock.

Asynchronous FIFO: separate clocks for read and write. Gray-code pointer encoding prevents metastability across the clock domain crossing. Required when the sensor pixel clock ≠ DMA bus clock (common in CSI-2 to AXI bridges).

---

**Q142: How does an FPGA implement a frame grabber for parallel interface sensors?**

1. Pixel clock (PCLK) drives the input shift register.
2. VSYNC and HSYNC detect frame and line boundaries.
3. Pixel data is written to a FIFO on each PCLK edge.
4. A DMA engine reads from the FIFO and writes to DDR via AXI interface.
5. When a complete frame is received, an interrupt is generated to the CPU.

---

# PART 2 — Image Sensor Specific (100 Questions)

**Q151: What is a rolling shutter vs. global shutter?**

Rolling shutter: each row is exposed at a slightly different time. Causes "jello effect" on fast-moving objects. Used in CMOS sensors with column-parallel ADCs (lower cost, power).

Global shutter: all pixels exposed simultaneously. Required for machine vision with fast-moving parts, strobe lighting, or stereo applications where synchronisation is critical. Implemented with in-pixel storage capacitor (more complex pixel design, higher cost).

---

**Q152: Explain the camera calibration parameters — intrinsics and extrinsics.**

Intrinsics: camera-specific parameters — focal length (fx, fy), principal point (cx, cy), distortion coefficients (k1, k2, k3 for radial, p1, p2 for tangential). Stored in EEPROM.

Extrinsics: camera position and orientation in world coordinates — rotation matrix R and translation vector t. For stereo, describes the baseline between cameras.

---

**Q153: What is ISP (Image Signal Processor) and what stages does it have?**

```
RAW sensor data →
Defect Pixel Correction →
Black Level Subtraction →
Lens Shading Correction →
Demosaicing (Bayer → RGB) →
White Balance →
Color Correction Matrix (CCM) →
Gamma Correction →
Noise Reduction →
Sharpening →
YUV/RGB conversion →
Compression (H.264/HEVC/JPEG)
```

---

**Q154: What is sensor saturation and how does it affect image quality?**

Saturation occurs when pixel well capacity (full well capacity, FWC) is exceeded — typically 10,000–100,000 electrons in modern sensors. Saturated pixels read as maximum value (white clipping). Effects: loss of detail in highlights, blooming into adjacent pixels in interline-transfer CCD sensors. Mitigation: reduce exposure, use ND filters, use HDR mode.

---

**Q155: How does on-chip embedded metadata work in Sony sensors?**

Sony IMX sensors embed metadata (statistics) in the first N rows of each frame as CSI-2 data type 0x12 (embedded data). The rows contain: histogram data, AE statistics, focus statistics, temperature, frame counter. The firmware / ISP must strip these rows before displaying the image, or parse them for AE/AF control loops.

---

# PART 3 — Debugging and Performance (90 Questions)

**Q251: How do you debug an intermittent frame drop?**

1. Add a frame sequence counter (sensor embeds it in metadata or host increments it).
2. Log sequence number with timestamp on every received frame.
3. Compare sequences — a gap indicates a drop.
4. For the dropped frame, check: DMA FIFO error register, CSI-2 error counter, free buffer pool count, CPU load during the drop window.
5. Most common causes: DMA starvation (buffer pool exhausted), CPU spike (other interrupt delaying DMA reprogramming), thermal throttling.

---

**Q252: A sensor reports higher-than-expected temperature. What do you investigate?**

1. Verify temperature register formula is correctly applied.
2. Check ambient temperature in the test environment.
3. Measure PCB temperature with an IR camera — compare to sensor embedded value.
4. Check if the sensor is streaming at full data rate (full-rate streaming significantly increases power).
5. Review power supply — VDD_IO noise can cause incorrect temperature reading.
6. Cross-validate with an external temperature sensor on the PCB.

---

**Q253: How do you identify if ECC errors are systematic or random?**

Random: ECC errors occur sporadically at low rates (< 1 per 1000 frames) — likely cosmic rays or thermal noise. Acceptable.

Systematic: ECC errors occur at a consistent rate on specific frames or line positions — indicates timing issue (D-PHY settle time marginal, PCB trace impedance mismatch, power supply noise at a specific frequency).

Diagnosis: capture a 10,000-frame sequence, record ECC error position in each frame. If errors cluster at the same byte offset in every frame, it is systematic.

---

**Q254: How do you measure DMA latency from ISR trigger to buffer ready?**

1. Assert a GPIO at the start of the CSI-2 interrupt (frame-complete ISR).
2. Assert another GPIO when the DMA completion ISR fires.
3. Use a logic analyser to measure the time between the two GPIOs.
4. For a production trace: embed GPIO timestamps in the trace logger and analyse the binary log.

---

**Q255: What tools do you use for embedded firmware profiling?**

| Tool | Method |
|---|---|
| SEGGER SystemView | RTOS-aware real-time profiler over J-Link |
| ARM ETM/ITM | Hardware trace unit, zero-overhead instruction tracing |
| GPIO toggle + oscilloscope | Quick worst-case timing measurement |
| Perf (Linux) | Linux perf_events for userspace and kernel profiling |
| Callgrind + Valgrind | Host-side simulation profiling |
| Custom cycle counter | Read SysTick or DWT_CYCCNT before/after function |

---

# PART 4 — Architecture Design Questions (30 Questions)

**Q291: Design a zero-copy streaming pipeline from MIPI CSI-2 to host PC over USB3.**

```
SENSOR (CSI-2, 2-lane, 1.5 Gbps)
    ↓ D-PHY
CSI-2 Receiver (FPGA / SoC)
    ↓ DMA (scatter-gather to DDR)
Frame Buffer Pool (DDR, 4×frame)  ← Firmware manages ownership
    ↓ Zero-copy pointer transfer
USB3 Controller DMA (reads from same buffer in DDR)
    ↓ USB3 Vision / UVC
Host PC buffer (mapped as DMA-BUF or USERP in V4L2)
    ↓ Application
OpenCV / HALCON / custom algorithm
```

Key design decisions:
- DDR buffer must be in a contiguous physical region accessible by both CSI-2 DMA and USB DMA.
- Triple-buffering minimum: while USB sends buffer N, CSI-2 fills buffer N+1, app has buffer N-1.
- `stream_return_frame()` must be called promptly to prevent starvation.
- USB bulk transfer with ZLP (zero-length packet) to terminate each frame.

---

**Q292: How do you design a multi-camera synchronization system?**

```
Master sensor: free-running, outputs FSIN/XVS on GPIO
    ↓ (hardware wire)
Slave sensors (1–N): XVS input, sync to master's frame timing

Master timing:
    FSIN pulse → all sensors expose simultaneously
    Frame N output: all CSI-2 frame starts within < 1 µs

Software:
    Each CSI-2 pipeline timestamps SOF from hardware counter
    Synchronization manager: groups frames by sequence number
    Reports max timestamp delta across sensors (should be < 1 frame period / 100)
```

---

**Q293: How would you implement a fault-tolerant sensor firmware with watchdog?**

```
Boot → Validate firmware CRC → Load calibration → Init sensor
                ↓
         Normal operation loop
                ↓
    Feed watchdog every 100 ms  ←────────┐
                ↓                        │
    If sensor I2C fails → retry 3× ──────┤
                ↓                        │
    If streaming drops → CSI2 reset ─────┤
                ↓                        │
    If temperature > 85°C → reduce FPS ──┘
                ↓
    If watchdog not fed → reset → safe boot
         (load minimal config, report DTC, wait for host command)
```

---

# PART 5 — System Integration (50 Questions)

**Q301: Walk through integrating a new CMOS sensor into the platform.**

1. **Obtain documentation**: datasheet, application note, register map, reference init table.
2. **Create driver skeleton**: implement `sensor_driver_t` ops, define chip ID and I2C address.
3. **Probe**: verify chip ID reads correctly over I2C. Check I2C bus speed (some sensors require slow bus at startup).
4. **Init table**: load manufacturer's recommended sequence, verify by reading a few registers back.
5. **Configure modes**: implement resolution/FPS configuration, verify correct frame dimensions from CSI-2 metadata.
6. **Gain/exposure**: implement control registers, verify with a calibrated integrating sphere or fixed illumination.
7. **Test pattern**: enable and verify each test pattern matches expected pixel values.
8. **Streaming**: verify zero ECC/CRC errors over 10,000 frames.
9. **Register the driver** with `sensor_register_driver()`.

---

**Q302: How do you verify the MIPI CSI-2 link is locked and healthy?**

1. Check D-PHY lane sync status register — all lanes must show ULPS-exit and SOT-detected.
2. Read error counters (ECC single/double, CRC, SOT leader, SOT sync) — all should be zero.
3. Verify frame counter increments with each received frame.
4. Enable sensor test pattern and verify pixel data matches.
5. Run at rated data rate for 1000 frames — zero errors expected.
6. Check receive FIFO level — should not exceed 50% at steady state.

---

*[Questions Q303–Q340 covering Ethernet, USB3 Vision, calibration, manufacturing, and deployment test procedures — available in the extended companion guide]*

---

# APPENDIX — Production Deployment Checklist

| Check | Criteria | Tool |
|---|---|---|
| Firmware CRC verify | Zero CRC errors on flash read-back | Bootloader |
| Sensor probe | Chip ID matches expected value | sensor_discover() |
| MIPI link quality | 0 ECC/CRC errors over 1000 frames | csi2_get_stats() |
| Temperature | < 70°C at max operating conditions | sensor_read_temperature() |
| Frame continuity | 0 sequence gaps over 10,000 frames | stream_get_stats() |
| Pixel blemish | < 0.1% dead/stuck pixels | Frame integrity test |
| Calibration | EEPROM checksum valid | sensor_read_eeprom() |
| OTA ready | Firmware package signed and verifiable | FirmwareUpdater |
| Latency | SOF → app dequeue < 50 ms | Performance test |
| Power | < specified TDP at full streaming | Current probe |
