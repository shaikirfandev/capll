// SPDX-License-Identifier: GPL-2.0-only
/*
 * sysfs_monitor.c — polls sensor_hub sysfs attributes periodically
 *
 * Reads rate, channel, status, threshold from sysfs every second.
 * Demonstrates the sysfs interface exposed by the driver.
 *
 * Build: gcc -O2 -Wall -o sysfs_monitor sysfs_monitor.c
 * Usage: ./sysfs_monitor [sysfs-dir]
 *   sysfs-dir default: /sys/bus/platform/devices/40080000.sensor-hub/sensor_hub
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>

static volatile int running = 1;
static void on_signal(int s) { (void)s; running = 0; }

static void read_attr(const char *dir, const char *attr, char *out, size_t sz)
{
    char path[512];
    int fd;
    ssize_t n;

    snprintf(path, sizeof(path), "%s/%s", dir, attr);
    fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        snprintf(out, sz, "(error)");
        return;
    }
    n = read(fd, out, sz - 1);
    close(fd);
    if (n > 0) {
        out[n] = '\0';
        /* strip trailing newline */
        char *nl = strchr(out, '\n');
        if (nl) *nl = '\0';
    } else {
        snprintf(out, sz, "(empty)");
    }
}

static void write_attr(const char *dir, const char *attr, const char *val)
{
    char path[512];
    int fd;

    snprintf(path, sizeof(path), "%s/%s", dir, attr);
    fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        perror(path);
        return;
    }
    write(fd, val, strlen(val));
    close(fd);
}

int main(int argc, char *argv[])
{
    const char *dir =
        "/sys/bus/platform/devices/40080000.sensor-hub/sensor_hub";

    if (argc > 1)
        dir = argv[1];

    signal(SIGINT,  on_signal);
    signal(SIGTERM, on_signal);

    printf("Monitoring sysfs: %s\n", dir);
    printf("(Ctrl-C to stop)\n\n");

    /* Demo: switch to channel 1, rate 200 Hz */
    write_attr(dir, "channel", "1");
    write_attr(dir, "rate",    "200");
    write_attr(dir, "threshold", "60000 1000");
    write_attr(dir, "enable",  "1");

    char rate[32], channel[32], status[128], threshold[64];

    while (running) {
        read_attr(dir, "rate",      rate,      sizeof(rate));
        read_attr(dir, "channel",   channel,   sizeof(channel));
        read_attr(dir, "status",    status,    sizeof(status));
        read_attr(dir, "threshold", threshold, sizeof(threshold));

        printf("rate=%-5s  ch=%-2s  threshold=[%s]  status: %s\n",
               rate, channel, threshold, status);

        sleep(1);
    }

    /* Restore defaults before exit */
    write_attr(dir, "channel", "0");
    write_attr(dir, "rate",    "100");
    write_attr(dir, "enable",  "0");

    printf("Done.\n");
    return 0;
}
