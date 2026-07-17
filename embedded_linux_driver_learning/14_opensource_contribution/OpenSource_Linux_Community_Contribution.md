# Linux Open Source Contribution — Community & Patch Submission

## Level 1: Understanding the Linux Community

### 1.1 Linux Development Model

```
Linus Torvalds (main kernel)
    │
    ├── Subsystem Maintainers (Greg KH, Dave Miller, etc.)
    │     Each owns a subtree (drivers/usb/, net/, sound/, etc.)
    │
    ├── Mailing Lists (LKML, DRI-devel, ALSA-devel, etc.)
    │     All development discussion is public
    │
    └── linux-next tree
          Integration tree for next merge window

Release Cycle (~9-10 weeks):
  Week 0–2:  Merge window (new features merged)
  Week 3–10: RC phase (rc1–rc7/8, bug fixes only)
  Week 10:   Final release (v6.X)
```

### 1.2 Key Mailing Lists by Domain

| Domain | Mailing List |
|--------|-------------|
| General/core | linux-kernel@vger.kernel.org (LKML) |
| Graphics (DRM) | dri-devel@lists.freedesktop.org |
| Audio (ALSA) | alsa-devel@alsa-project.org |
| Networking | netdev@vger.kernel.org |
| V4L2/media | linux-media@vger.kernel.org |
| Embedded/ARM | linux-arm-kernel@lists.infradead.org |
| USB | linux-usb@vger.kernel.org |
| Power mgmt | linux-pm@vger.kernel.org |
| Yocto | yocto@yoctoproject.org |

---

## Level 2: Setting Up for Contribution

### 2.1 Git Configuration

```bash
# Essential git config for kernel work
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Configure send-email
git config --global sendemail.smtpserver smtp.gmail.com
git config --global sendemail.smtpserverport 587
git config --global sendemail.smtpencryption tls
git config --global sendemail.smtpuser your@email.com

# Verify email is set (must match kernel.org account)
git config user.email
```

### 2.2 Finding Your First Patch

```bash
# Good first contributions:
# 1. Fix a checkpatch warning
# 2. Fix a coccinelle warning
# 3. Fix a sparse warning
# 4. Fix a typo in documentation
# 5. Add missing OF match table or MODULE_DEVICE_TABLE
# 6. Convert kmalloc + memset to kzalloc
# 7. Fix a kerneldoc comment

# Find checkpatch issues in a driver file
./scripts/checkpatch.pl --strict drivers/your-driver.c

# Find coccinelle issues
./scripts/coccinelle/api/kzalloc-simple.cocci

# Find missing SPDX headers
grep -r "SPDX-License" drivers/your-area/ | wc -l

# Kernel janitors list: https://kernelnewbies.org/KernelJanitors
# Easy bugs: https://bugzilla.kernel.org (filter: "easy")
```

---

## Level 3: Writing a Kernel Patch

### 3.1 Making a Good Commit

```bash
# Always work on top of mainline or a subsystem tree
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux
git checkout -b my-fix

# Make your change
vim drivers/my-driver/my-driver.c

# Test it (build + run)
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- my-driver.ko
# or
make -j8

# Check style
./scripts/checkpatch.pl --strict -g HEAD

# Check sparse (semantic C checking)
make C=1 drivers/my-driver/my-driver.ko

# Check smatch
make CHECK="smatch -p=kernel" C=1 drivers/my-driver/my-driver.ko

# Commit with proper format
git add drivers/my-driver/my-driver.c
git commit
```

### 3.2 Commit Message Format

```
subsystem: component: brief description (max 70 chars)

Long description of what changed and WHY.
Focus on the WHY — the code shows the WHAT.

Explanation of the bug or motivation.
How the fix works.
Any side effects or related changes.

Link: https://lore.kernel.org/... (if fixing a reported bug)
Reported-by: John Doe <john@example.com>
Fixes: abc123def456 ("commit that introduced the bug")
Signed-off-by: Your Name <your@email.com>
```

**Real Examples:**
```
drm/panfrost: Fix race in job completion handling

When a job completes, the IRQ handler clears the hardware status
register and calls drm_sched_job_done(). However, if another thread
is checking the job status via the sched_job_hw_fence, a race can
occur where the job appears completed before the fence is signaled.

Fix this by holding the scheduler lock during fence signaling.

Fixes: 8f4d2b7a1234 ("drm/panfrost: Add job scheduling")
Reported-by: Alice Smith <alice@kernel.org>
Signed-off-by: Bob Jones <bob@kernel.org>
```

```
net: my_driver: Use devm_clk_get_enabled() helper

Replace the open-coded clk_get() + clk_prepare_enable() pair
with the single devm_clk_get_enabled() helper which handles
cleanup automatically on device removal.

No functional change.

Signed-off-by: Your Name <your@email.com>
```

---

## Level 4: Sending Patches

### 4.1 Format and Send

```bash
# Format patch (generates .patch files)
git format-patch -1 HEAD                   # last commit
git format-patch HEAD~3..HEAD              # last 3 commits
git format-patch -3 --cover-letter HEAD    # with cover letter

# Check format
cat 0001-my-fix.patch
./scripts/checkpatch.pl 0001-my-fix.patch

# Find correct maintainers
./scripts/get_maintainer.pl 0001-my-fix.patch
# Output:
# John Doe <john@kernel.org> (maintainer:MY_DRIVER)
# Jane Smith <jane@kernel.org> (reviewer)
# linux-kernel@vger.kernel.org (open list)
# linux-arm-kernel@lists.infradead.org (open list:ARM...)

# Send the patch
git send-email \
    --to "John Doe <john@kernel.org>" \
    --cc "Jane Smith <jane@kernel.org>" \
    --cc linux-kernel@vger.kernel.org \
    0001-my-fix.patch

# Patch series (multiple commits)
git format-patch -3 --cover-letter HEAD
# Edit 0000-cover-letter.patch
git send-email \
    --to maintainer@kernel.org \
    --cc linux-kernel@vger.kernel.org \
    0000-cover-letter.patch \
    0001-first-fix.patch \
    0002-second-fix.patch \
    0003-third-fix.patch
```

### 4.2 Responding to Review

```bash
# Reviewer sends comments → You reply on the mailing list
# Reply inline to the specific line of feedback

# v2 patch after incorporating feedback
git format-patch -1 HEAD --subject-prefix="PATCH v2"
# Edit commit message to add:
# Changes in v2:
#   - Use devm_ variant instead of manual cleanup
#   - Add missing error check for ioremap
#   - Fix style issue in comment

# Reply to original thread (preserves threading)
git send-email \
    --in-reply-to <message-id-of-v1> \
    --to maintainer@kernel.org \
    0001-my-fix-v2.patch
```

---

## Level 5: Real Contribution Workflow

### 5.1 Finding a Real Driver to Fix

```bash
# Find TODO/FIXME comments in drivers
grep -r "TODO\|FIXME\|HACK\|XXX" drivers/gpu/drm/panfrost/ | head -20

# Find deprecated API usage
grep -r "pci_enable_device\b" drivers/ | grep -v "pcim_enable_device"
# This finds drivers that use old pci_enable_device() instead of pcim_ variant

# Find missing SPDX identifiers  
grep -rL "SPDX-License-Identifier" drivers/media/ | head -10

# Find sparse warnings
make ARCH=arm64 C=1 drivers/net/ethernet/... 2>&1 | grep "warning:"
```

### 5.2 Submitting a New Driver

```
New driver checklist:
□ Driver compiles cleanly (no warnings)
□ Passes checkpatch --strict
□ Passes sparse (make C=1)
□ Has proper SPDX-License-Identifier
□ Has MODULE_LICENSE, MODULE_AUTHOR, MODULE_DESCRIPTION
□ Uses devm_ variants where possible
□ Has Device Tree binding documentation
□ Binding validated with: dt_binding_check
□ Has Kconfig entry with description
□ Has entry in MAINTAINERS file
□ Tested on actual hardware
□ Tested suspend/resume
□ No lockdep warnings
□ No KASAN warnings
□ Documentation/devicetree/bindings/ patch included
```

### 5.3 Device Tree Binding Documentation

```yaml
# Documentation/devicetree/bindings/my-subsystem/vendor,my-device.yaml

%YAML 1.2
---
$id: http://devicetree.org/schemas/my-subsystem/vendor,my-device.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Vendor My Device Controller

maintainers:
  - Your Name <your@email.com>

properties:
  compatible:
    enum:
      - vendor,my-device-v1
      - vendor,my-device-v2

  reg:
    maxItems: 1

  interrupts:
    maxItems: 1

  clocks:
    items:
      - description: Core clock
      - description: Bus clock

  clock-names:
    items:
      - const: core
      - const: bus

required:
  - compatible
  - reg
  - interrupts
  - clocks
  - clock-names

additionalProperties: false

examples:
  - |
    my_device: controller@40000000 {
      compatible = "vendor,my-device-v1";
      reg = <0x40000000 0x1000>;
      interrupts = <GIC_SPI 55 IRQ_TYPE_LEVEL_HIGH>;
      clocks = <&ccu 0>, <&ccu 1>;
      clock-names = "core", "bus";
    };
```

---

## Level 6: Kernel Review Etiquette

```
DO:
  ✓ Reply to ALL reviewers, not just the maintainer
  ✓ Be patient — maintainers are volunteers
  ✓ Address EVERY review comment (or explain why not)
  ✓ Add "Reviewed-by:" and "Acked-by:" tags from reviewer emails
  ✓ CC the people who gave Reviewed-by on subsequent versions
  ✓ Test your patch on actual hardware
  ✓ Wait 2 weeks before pinging on status

DON'T:
  ✗ Send HTML email (plain text only)
  ✗ Top-post (reply inline, below the quoted text)
  ✗ Send to mailing list AND CC individuals excessively
  ✗ Argue aggressively with reviewers
  ✗ Send patches without subject prefix ("PATCH" or "RFC PATCH")
  ✗ Use "git format-patch --thread" (threading is auto)
```

---

## Level 7: Tags Reference

```
Signed-off-by:  Author/committer agrees with Developer Certificate of Origin (DCO)
Acked-by:       Subsystem maintainer OK'd but won't merge
Reviewed-by:    Reviewer verified correctness
Tested-by:      Someone tested the patch on hardware
Reported-by:    Person who reported the bug (get their permission)
Fixes:          SHA1 of the commit that introduced the bug
Link:           URL to related discussion/bug report
Co-developed-by: Co-author of the patch

# DCO (Developer Certificate of Origin):
# Signing off means you have the right to submit this code
# and agree to the rules at https://developercertificate.org
```

---

## Useful Resources

```
Kernelnewbies:    https://kernelnewbies.org/
Kernel docs:      https://kernel.org/doc/html/latest/process/
Patchwork:        https://patchwork.kernel.org/ (track patch status)
lore.kernel.org:  https://lore.kernel.org/ (searchable mailing list archive)
Smatch:           https://smatch.sourceforge.net/
Coccinelle:       https://coccinelle.lip6.fr/
Bootlin slides:   https://bootlin.com/training/

Recommended reading:
  Documentation/process/submitting-patches.rst
  Documentation/process/coding-style.rst
  Documentation/process/maintainer-tip.rst
  Documentation/process/email-clients.rst
```

---

## Interview Questions

1. What is the Linux kernel development process? How are patches merged?
2. What is DCO (Developer Certificate of Origin)?
3. What does `Signed-off-by` mean?
4. How do you find the right maintainer for your patch?
5. What is `checkpatch.pl` and when do you run it?
6. What is `sparse` and what does it check?
7. How do you submit a patch series with multiple commits?
8. What is patchwork.kernel.org used for?
9. What is the difference between `Reviewed-by` and `Acked-by`?
10. How do you handle reviewer feedback across multiple patch versions?
