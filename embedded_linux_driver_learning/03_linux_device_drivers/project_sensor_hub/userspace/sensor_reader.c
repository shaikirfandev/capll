// SPDX-License-Identifier: GPL-2.0-only
/*
 * sensor_reader.c — userspace application for sensor_hub driver
 *
 * Demonstrates:
 *   - Opening /dev/sensor_hub0
 *   - ioctl: set channel, rate, calibration
 *   - Blocking read() of sh_sample structs
 *   - ioctl: burst DMA read
 *   - poll() to check availability before read
 *
 * Build: gcc -O2 -Wall -o sensor_reader sensor_reader.c
 * Usage: ./sensor_reader [/dev/sensor_hub0]
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <stdint.h>

/* Pull in the shared header (same as kernel uses) */
#include "../kernel/sensor_hub.h"

static volatile int running = 1;
static void on_signal(int s) { (void)s; running = 0; }

/* Print one sample in human-readable form */
static void print_sample(const struct sh_sample *s)
{
    printf("[ch%u] raw=%-6u  ts=%llu ns  flags=0x%02x%s%s\n",
           s->channel,
           s->value,
           (unsigned long long)s->timestamp_ns,
           s->flags,
           (s->flags & 0x04) ? " THR_HI" : "",
           (s->flags & 0x08) ? " THR_LO" : "");
}

int main(int argc, char *argv[])
{
    const char *dev = "/dev/sensor_hub0";
    int fd, ret;
    struct sh_sample samples[16];
    ssize_t n;

    if (argc > 1)
        dev = argv[1];

    signal(SIGINT,  on_signal);
    signal(SIGTERM, on_signal);

    fd = open(dev, O_RDWR | O_CLOEXEC);
    if (fd < 0) {
        perror("open");
        return 1;
    }
    printf("Opened %s\n", dev);

    /* ── Configure the hardware via ioctl ── */

    /* Select channel 0 (temperature) */
    uint32_t ch = 0;
    if (ioctl(fd, SH_IOC_SET_CHANNEL, &ch) < 0) {
        perror("SH_IOC_SET_CHANNEL");
        goto out;
    }

    /* Set sample rate to 50 Hz */
    uint32_t rate = 50;
    if (ioctl(fd, SH_IOC_SET_RATE, &rate) < 0) {
        perror("SH_IOC_SET_RATE");
        goto out;
    }

    /* Set calibration offset for channel 0 */
    struct sh_cal cal = { .channel = 0, .offset = -12 };
    if (ioctl(fd, SH_IOC_SET_CAL, &cal) < 0)
        perror("SH_IOC_SET_CAL (non-fatal)");

    /* Set thresholds: IRQ when sample > 60000 or < 1000 */
    /* (via sysfs instead — shows both paths are usable) */
    printf("Thresholds set via sysfs. Configure with:\n");
    printf("  echo '60000 1000' > "
           "/sys/bus/platform/devices/40080000.sensor-hub/sensor_hub/threshold\n\n");

    /* ── Demo 1: burst DMA read of 32 samples ── */
    printf("=== Burst DMA read (32 samples) ===\n");
    uint16_t burst_buf[32] = {0};
    struct sh_burst_req req = {
        .count  = 32,
        .buf    = burst_buf,
        .actual = 0,
    };
    if (ioctl(fd, SH_IOC_BURST_READ, &req) == 0) {
        uint32_t i;
        printf("Got %u samples from FIFO:\n", req.actual);
        for (i = 0; i < req.actual; i++)
            printf("  [%02u] %u\n", i, burst_buf[i]);
    } else {
        perror("SH_IOC_BURST_READ (non-fatal)");
    }

    /* ── Demo 2: blocking read() loop using poll() ── */
    printf("\n=== Blocking read loop (Ctrl-C to stop) ===\n");

    struct pollfd pfd = { .fd = fd, .events = POLLIN };

    while (running) {
        /* Wait up to 2 seconds for a sample */
        ret = poll(&pfd, 1, 2000);
        if (ret < 0) {
            if (errno == EINTR)
                break;
            perror("poll");
            break;
        }
        if (ret == 0) {
            printf("(timeout — no sample in 2s)\n");
            continue;
        }

        /* Read as many samples as available (up to 16 at a time) */
        n = read(fd, samples, sizeof(samples));
        if (n < 0) {
            if (errno == EAGAIN)
                continue;
            perror("read");
            break;
        }

        size_t count = (size_t)n / sizeof(struct sh_sample);
        size_t i;
        for (i = 0; i < count; i++)
            print_sample(&samples[i]);
    }

    /* ── Demo 3: flush FIFO before exit ── */
    if (ioctl(fd, SH_IOC_FLUSH_FIFO) < 0)
        perror("SH_IOC_FLUSH_FIFO (non-fatal)");

    printf("\nDone.\n");

out:
    close(fd);
    return 0;
}
