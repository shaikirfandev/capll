/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * sensor_hub.h — Register map, data structures, and ioctl interface
 *                for the Industrial Sensor Hub platform driver.
 */

#ifndef _SENSOR_HUB_H
#define _SENSOR_HUB_H

#include <linux/ioctl.h>
#include <linux/types.h>

/* ------------------------------------------------------------------ */
/*  MMIO Register offsets                                               */
/* ------------------------------------------------------------------ */

#define SH_CTRL         0x000   /* Control register (rw) */
#define SH_STATUS       0x004   /* Status register  (ro) */
#define SH_CH_SEL       0x008   /* Channel select   (rw, bits [1:0]) */
#define SH_DATA         0x00C   /* Single sample    (ro, 16-bit, read-clears) */
#define SH_FIFO_LVL     0x010   /* FIFO fill level  (ro) */
#define SH_FIFO_DATA    0x014   /* FIFO burst port  (ro) */
#define SH_RATE         0x018   /* Sample rate Hz   (rw, 1–1000) */
#define SH_THR_HI       0x01C   /* High threshold   (rw) */
#define SH_THR_LO       0x020   /* Low threshold    (rw) */
#define SH_CAL_BASE     0x100   /* Cal offsets[4]   (rw, 4 × u32) */

/* SH_CTRL bit fields */
#define SH_CTRL_ENABLE          BIT(0)  /* global enable */
#define SH_CTRL_RESET           BIT(1)  /* self-clearing reset */
#define SH_CTRL_IRQ_DATA_RDY    BIT(2)  /* enable data-ready IRQ */
#define SH_CTRL_IRQ_OVERFLOW    BIT(3)  /* enable FIFO overflow IRQ */
#define SH_CTRL_IRQ_THR         BIT(4)  /* enable threshold IRQ */
#define SH_CTRL_DMA_EN          BIT(5)  /* enable DMA FIFO drain */

/* SH_STATUS bit fields */
#define SH_STATUS_DATA_RDY      BIT(0)  /* a sample is ready */
#define SH_STATUS_OVERFLOW      BIT(1)  /* FIFO overflowed */
#define SH_STATUS_THR_HI        BIT(2)  /* sample exceeded THR_HI */
#define SH_STATUS_THR_LO        BIT(3)  /* sample fell below THR_LO */
#define SH_STATUS_IRQ_PENDING   BIT(4)  /* any IRQ pending (write 1 to clear) */

/* Number of hardware channels */
#define SH_NUM_CHANNELS         4

/* Maximum FIFO depth (samples) */
#define SH_FIFO_DEPTH           256

/* DMA buffer: enough for a full FIFO */
#define SH_DMA_BUF_SAMPLES      SH_FIFO_DEPTH
#define SH_DMA_BUF_BYTES        (SH_DMA_BUF_SAMPLES * sizeof(u16))

/* ------------------------------------------------------------------ */
/*  ioctl interface (used by userspace sensor_reader)                   */
/* ------------------------------------------------------------------ */

#define SH_IOC_MAGIC  's'

/* Set active channel (0–3) */
#define SH_IOC_SET_CHANNEL      _IOW(SH_IOC_MAGIC, 1, __u32)

/* Get active channel */
#define SH_IOC_GET_CHANNEL      _IOR(SH_IOC_MAGIC, 2, __u32)

/* Set sample rate (Hz, 1–1000) */
#define SH_IOC_SET_RATE         _IOW(SH_IOC_MAGIC, 3, __u32)

/* Get sample rate */
#define SH_IOC_GET_RATE         _IOR(SH_IOC_MAGIC, 4, __u32)

/* Flush the hardware FIFO */
#define SH_IOC_FLUSH_FIFO       _IO(SH_IOC_MAGIC,  5)

/* Set calibration offset for a channel */
struct sh_cal {
    __u32 channel;  /* 0–3 */
    __s32 offset;   /* signed calibration offset, raw units */
};
#define SH_IOC_SET_CAL          _IOW(SH_IOC_MAGIC, 6, struct sh_cal)
#define SH_IOC_GET_CAL          _IOWR(SH_IOC_MAGIC, 7, struct sh_cal)

/* Read a burst of N samples synchronously via DMA */
struct sh_burst_req {
    __u32  count;       /* in:  how many samples to read */
    __u16 *buf;         /* in:  userspace buffer pointer */
    __u32  actual;      /* out: samples actually read */
};
#define SH_IOC_BURST_READ       _IOWR(SH_IOC_MAGIC, 8, struct sh_burst_req)

#define SH_IOC_MAXNR  8

/* ------------------------------------------------------------------ */
/*  Sample structure returned by read(2)                               */
/* ------------------------------------------------------------------ */

/* Each read(2) on /dev/sensor_hubN returns one or more of these */
struct sh_sample {
    __u16   value;          /* raw ADC value (calibration already applied) */
    __u8    channel;        /* which channel (0–3) */
    __u8    flags;          /* SH_STATUS bits at capture time */
    __u32   reserved;       /* pad to 8 bytes */
    __u64   timestamp_ns;   /* ktime_get_ns() at IRQ time */
};

#endif /* _SENSOR_HUB_H */
