CC      ?= gcc
CFLAGS  := -O2 -Wall -Wextra -Werror -I../kernel
TARGETS := sensor_reader sysfs_monitor

.PHONY: all clean

all: $(TARGETS)

sensor_reader: sensor_reader.c ../kernel/sensor_hub.h
	$(CC) $(CFLAGS) $< -o $@

sysfs_monitor: sysfs_monitor.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f $(TARGETS)
