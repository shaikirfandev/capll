# Kernel module Makefile
# Usage:
#   make KDIR=/lib/modules/$(uname -r)/build               # native
#   make KDIR=/path/to/kernel ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-

KDIR ?= /lib/modules/$(shell uname -r)/build

obj-m := sensor_hub.o

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a
