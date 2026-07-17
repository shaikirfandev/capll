# Yocto Development — From Basic to Advanced

## Level 1: Yocto/BitBake Basics

### 1.1 What is Yocto?

```
Yocto Project = Build framework for custom embedded Linux
    ├── Poky          — reference distribution
    ├── BitBake       — build engine (task scheduler)
    ├── OpenEmbedded  — recipe/layer collection
    └── meta-*        — layers (BSP layers, feature layers)

Output:
    ├── Linux kernel image  (Image, zImage, uImage)
    ├── Rootfs              (ext4, squashfs, initramfs)
    ├── DTBs                (device tree blobs)
    ├── SDK                 (cross-compiler + sysroot)
    └── Package feeds       (ipk, rpm, deb)
```

### 1.2 First Build

```bash
# Setup
git clone git://git.yoctoproject.org/poky
cd poky
git checkout kirkstone    # or dunfell, scarthgap, etc.

# Setup build environment
source oe-init-build-env build/

# Configure (edit conf/local.conf)
MACHINE = "qemux86-64"     # or raspberrypi4, beaglebone, etc.
DISTRO = "poky"
# Parallelism
BB_NUMBER_THREADS = "8"
PARALLEL_MAKE = "-j8"

# Build minimal image
bitbake core-image-minimal

# Build full image with dev tools
bitbake core-image-full-cmdline

# Run in QEMU
runqemu qemux86-64

# Artifacts location
ls tmp/deploy/images/qemux86-64/
```

### 1.3 BitBake Concepts

```
Recipe (.bb):
  Describes HOW to build one package
  → fetch sources
  → configure
  → compile
  → install
  → package

Layer (meta-*):
  Collection of recipes, configuration, bbclasses

Image (.bb in recipes-core/images/):
  Special recipe that defines rootfs contents
  → lists packages to include

bbclass (.bbclass):
  Shared functionality (cmake, autotools, kernel-module, etc.)

MACHINE:
  Hardware target (defines arch, kernel, bootloader)

DISTRO:
  Distribution policy (libc, init system, features)
```

---

## Level 2: Writing Recipes

### 2.1 Basic Application Recipe

```bitbake
# File: meta-my-layer/recipes-apps/my-app/my-app_1.0.bb

SUMMARY = "My custom application"
DESCRIPTION = "Application that does X and Y"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=b234ee4d69f5fce4486a80fdaf4a4263"

# Source from local files
SRC_URI = "file://main.c \
           file://Makefile \
          "

# Or from git
SRC_URI = "git://github.com/user/repo.git;protocol=https;branch=main"
SRCREV = "abc123def456..."

S = "${WORKDIR}"

# Or for git:
S = "${WORKDIR}/git"

do_compile() {
    oe_runmake CC="${CC}" CFLAGS="${CFLAGS}"
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 my-app ${D}${bindir}/my-app

    install -d ${D}${sysconfdir}/my-app
    install -m 0644 ${WORKDIR}/my-app.conf ${D}${sysconfdir}/my-app/
}

# Add to package
FILES_${PN} = "${bindir}/my-app ${sysconfdir}/my-app"
```

### 2.2 Kernel Module Recipe

```bitbake
# File: meta-my-layer/recipes-kernel/my-driver/my-driver_1.0.bb

SUMMARY = "My kernel driver"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=..."

inherit module

SRC_URI = "file://my_driver.c \
           file://Kbuild \
          "

S = "${WORKDIR}"

RPROVIDES_${PN} += "kernel-module-my-driver"
```

```makefile
# Kbuild file
obj-m := my_driver.o
```

### 2.3 autotools Recipe

```bitbake
inherit autotools pkgconfig

SRC_URI = "https://example.com/my-lib-${PV}.tar.gz"
SRC_URI[md5sum] = "abc..."
SRC_URI[sha256sum] = "def..."

PACKAGECONFIG[ssl] = "--enable-ssl,--disable-ssl,openssl"
PACKAGECONFIG[docs] = "--enable-docs,--disable-docs,doxygen"

EXTRA_OECONF = "--disable-tests --enable-shared"

DEPENDS = "zlib curl"           # build-time deps
RDEPENDS_${PN} = "libcurl"      # runtime deps
```

### 2.4 CMake Recipe

```bitbake
inherit cmake

SRC_URI = "git://github.com/user/project.git;branch=main"
SRCREV = "abc123"

S = "${WORKDIR}/git"

EXTRA_OECMAKE = "-DBUILD_TESTS=OFF -DENABLE_SHARED=ON"

DEPENDS = "boost protobuf"
```

---

## Level 3: Layer Creation

### 3.1 Create a Custom Layer

```bash
# Create layer structure
bitbake-layers create-layer ../meta-my-layer
cd ../meta-my-layer

# Layer structure
meta-my-layer/
├── conf/
│   ├── layer.conf          ← layer configuration
│   └── machine/
│       └── my-machine.conf ← machine definition (if BSP layer)
├── recipes-core/
│   └── images/
│       └── my-image.bb     ← custom image
├── recipes-kernel/
│   └── linux-my/
│       └── linux-my_5.15.bb  ← kernel recipe
├── recipes-apps/
│   └── my-app/
│       └── my-app_1.0.bb
└── recipes-bsp/
    └── u-boot/
        └── u-boot_%.bbappend ← kernel recipe override

# layer.conf
BBPATH .= ":${LAYERDIR}"
BBFILES += "${LAYERDIR}/recipes-*/*/*.bb ${LAYERDIR}/recipes-*/*/*.bbappend"
BBFILE_COLLECTIONS += "my-layer"
BBFILE_PATTERN_my-layer = "^${LAYERDIR}/"
BBFILE_PRIORITY_my-layer = "10"
LAYERDEPENDS_my-layer = "core"
LAYERSERIES_COMPAT_my-layer = "kirkstone scarthgap"

# Add layer to build
bitbake-layers add-layer ../meta-my-layer
# or edit bblayers.conf manually
```

---

## Level 4: Custom Kernel Recipe

### 4.1 Kernel Recipe

```bitbake
# File: meta-my-layer/recipes-kernel/linux/linux-my_5.15.bb

require recipes-kernel/linux/linux-yocto.inc

KBRANCH = "v5.15/standard/base"
SRCREV_machine = "abc123..."

SRC_URI = "git://git.yoctoproject.org/linux-yocto;branch=${KBRANCH};name=machine \
           file://my_defconfig \
           file://my-driver.cfg \
          "

# Kernel config fragment
# my-driver.cfg contains:
# CONFIG_MY_DRIVER=m
# CONFIG_MY_DRIVER_DEBUG=y

LINUX_VERSION ?= "5.15.30"
LINUX_VERSION_EXTENSION = "-my"

COMPATIBLE_MACHINE = "my-machine"

do_configure_prepend() {
    # Copy defconfig
    cp ${WORKDIR}/my_defconfig ${B}/.config
}
```

### 4.2 .bbappend for Kernel Customization

```bitbake
# File: recipes-kernel/linux/linux-yocto_5.15.bbappend

FILESEXTRAPATHS_prepend := "${THISDIR}/files:"

SRC_URI += "file://enable-can.cfg \
            file://enable-gpu.cfg \
            file://my-board.dts \
           "

# Add device tree
do_configure_append() {
    cp ${WORKDIR}/my-board.dts ${S}/arch/arm64/boot/dts/my-vendor/
}
```

---

## Level 5: Custom Image & SDK

### 5.1 Custom Image Recipe

```bitbake
# File: recipes-core/images/my-automotive-image.bb

require recipes-core/images/core-image-minimal.bb

IMAGE_FEATURES += "ssh-server-openssh debug-tweaks"

IMAGE_INSTALL += " \
    my-app \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    libv4l \
    alsa-utils \
    can-utils \
    i2c-tools \
    devmem2 \
    strace \
    gdb \
    perf \
    kernel-modules \
    "

# Image type
IMAGE_FSTYPES = "ext4 wic"

# Image size
IMAGE_ROOTFS_EXTRA_SPACE = "524288"   # 512 MB extra
```

### 5.2 SDK Generation

```bash
# Generate cross-compilation SDK
bitbake my-automotive-image -c populate_sdk

# SDK installer location
ls tmp/deploy/sdk/
# poky-glibc-x86_64-my-automotive-image-cortexa53-my-machine-toolchain-4.0.sh

# Install SDK
./poky-glibc-x86_64-...-toolchain-4.0.sh -d /opt/sdk/

# Use SDK
source /opt/sdk/environment-setup-cortexa53-poky-linux
echo $CC
# aarch64-poky-linux-gcc -mcpu=cortex-a53 ...

# Build application with SDK
$CC -o my_app my_app.c $CFLAGS $LDFLAGS
```

---

## Level 6: MACHINE Configuration (BSP Layer)

```bitbake
# conf/machine/my-imx8.conf

#@TYPE: Machine
#@NAME: My i.MX8 Board
#@DESCRIPTION: My custom i.MX8 based board

require conf/machine/include/arm/armv8a/tune-cortexa53.inc

MACHINE_FEATURES = "usbhost usbgadget alsa screen wifi bluetooth pci"

KERNEL_IMAGETYPE = "Image"
KERNEL_DEVICETREE = "freescale/imx8mm-my-board.dtb"

PREFERRED_PROVIDER_virtual/kernel = "linux-imx"
PREFERRED_VERSION_linux-imx = "5.15%"

UBOOT_MACHINE = "my_imx8_defconfig"
PREFERRED_PROVIDER_virtual/bootloader = "u-boot-imx"

SERIAL_CONSOLES = "115200;ttymxc1"

IMAGE_BOOT_FILES = "Image imx8mm-my-board.dtb"

# WIC image layout
WKS_FILE = "my-imx8-sdcard.wks"
```

---

## BitBake Key Commands

```bash
# Build
bitbake <recipe>                    # build recipe
bitbake <image>                     # build complete image
bitbake -c compile <recipe>         # run only compile task
bitbake -c clean <recipe>           # clean recipe build
bitbake -c cleanall <recipe>        # clean + remove downloads
bitbake -c fetch <recipe>           # only fetch sources

# Debug
bitbake -v <recipe>                 # verbose output
bitbake -DDD <recipe>               # debug level 3
bitbake world --dry-run             # show what would be built

# Inspection
bitbake -e <recipe> | grep ^WORKDIR  # show variable value
bitbake -e <recipe> > env.txt        # dump full environment
bitbake-layers show-recipes          # list all available recipes
bitbake-layers show-overlayed        # show overridden recipes

# Dependency graph
bitbake -g <recipe>                  # generates task-depends.dot
dot -Tpng task-depends.dot > deps.png

# devshell — interactive shell in recipe environment
bitbake -c devshell <recipe>

# devpyshell — Python shell in recipe environment
bitbake -c devpyshell <recipe>
```

---

## Interview Questions

1. What is the difference between a recipe (.bb) and a bbappend file?
2. Explain `DEPENDS` vs `RDEPENDS`.
3. What is a layer and how are layer priorities resolved?
4. How do you add a kernel config fragment in Yocto?
5. What does `inherit autotools` do?
6. How do you build a kernel module as a Yocto recipe?
7. What is `MACHINE_FEATURES` vs `DISTRO_FEATURES`?
8. How do you create a minimal rootfs image?
9. What is an SDK and how do you use it for native development?
10. How does Yocto handle recipe overrides (bbappend)?
