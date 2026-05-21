#!/usr/bin/env bash
# =============================================================================
# setup_rt_linux.sh — Configure a Linux system for PREEMPT_RT real-time use
# =============================================================================
# Run as root ONCE on the target system before launching the ADAS application.
#
# What this script does:
#   1.  Verifies PREEMPT_RT kernel is running
#   2.  Sets CPU isolation (isolcpus) in /etc/default/grub
#   3.  Disables CPU frequency scaling (sets performance governor)
#   4.  Configures IRQ affinity (move IRQs away from isolated CPUs)
#   5.  Sets real-time process limits in /etc/security/limits.conf
#   6.  Creates vcan0 virtual CAN interface for SIL testing
#   7.  Disables hyperthreading on isolated cores (optional)
#
# Tested on: Ubuntu 22.04 LTS + kernel 5.15-rt (lowlatency)
# =============================================================================

set -euo pipefail

# ── Target CPUs for ADAS RT threads ──────────────────────────────────────────
RT_CPUS="2,3"          # Isolated for ADAS (adjust to your platform)
HOUSEKEEPING_CPUS="0,1" # OS + IRQ handling

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

require_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# ── 1. Verify PREEMPT_RT kernel ──────────────────────────────────────────────
check_preempt_rt() {
    log_info "Checking kernel real-time support..."
    local kernel_ver
    kernel_ver=$(uname -r)

    if uname -v | grep -q "PREEMPT_RT\|PREEMPT RT"; then
        log_info "PREEMPT_RT kernel detected: $kernel_ver"
    else
        log_warn "PREEMPT_RT not detected in kernel $kernel_ver"
        log_warn "Install: sudo apt install linux-image-\$(uname -r)-rt"
        log_warn "Continuing without PREEMPT_RT (latency will be higher)"
    fi
}

# ── 2. Configure isolcpus in GRUB ─────────────────────────────────────────────
configure_isolcpus() {
    log_info "Configuring CPU isolation (isolcpus=${RT_CPUS})..."
    local grub_file="/etc/default/grub"

    if grep -q "isolcpus" "$grub_file"; then
        log_warn "isolcpus already set in $grub_file — skipping"
        return
    fi

    # Add to GRUB_CMDLINE_LINUX_DEFAULT
    sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"/GRUB_CMDLINE_LINUX_DEFAULT=\"isolcpus=${RT_CPUS} nohz_full=${RT_CPUS} rcu_nocbs=${RT_CPUS} /" "$grub_file"
    update-grub
    log_warn "GRUB updated. Reboot required for isolcpus to take effect."
}

# ── 3. CPU frequency governor → performance ───────────────────────────────────
set_performance_governor() {
    log_info "Setting CPU frequency governor to 'performance'..."
    if ! command -v cpufreq-set &>/dev/null; then
        apt-get install -y cpufrequtils 2>/dev/null || true
    fi

    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo "performance" > "$cpu" 2>/dev/null || true
    done

    # Disable Intel p-state turbo (prevents frequency variation under load)
    if [[ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]]; then
        echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo
        log_info "Intel Turbo Boost disabled"
    fi

    log_info "CPU governor: performance"
}

# ── 4. IRQ affinity: move interrupts away from RT CPUs ────────────────────────
configure_irq_affinity() {
    log_info "Setting IRQ affinity (keeping IRQs on CPUs ${HOUSEKEEPING_CPUS})..."

    # Compute housekeeping CPU mask (CPUs 0,1 → mask=0x3)
    local mask="3"

    for irq_dir in /proc/irq/*/; do
        local smp_file="${irq_dir}smp_affinity"
        if [[ -f "$smp_file" ]]; then
            echo "$mask" > "$smp_file" 2>/dev/null || true
        fi
    done

    log_info "IRQ affinity configured"
}

# ── 5. RT process limits ──────────────────────────────────────────────────────
configure_rt_limits() {
    log_info "Configuring real-time limits in /etc/security/limits.conf..."
    local limits_file="/etc/security/limits.conf"
    local entry="@adas_rt  -  rtprio  99
@adas_rt  -  memlock  unlimited
@adas_rt  -  nice     -20"

    if grep -q "adas_rt" "$limits_file"; then
        log_warn "RT limits already configured"
        return
    fi

    echo "$entry" >> "$limits_file"

    # Create the group if it doesn't exist
    groupadd -f adas_rt
    log_info "Add your user to adas_rt group: sudo usermod -aG adas_rt \$USER"
}

# ── 6. Virtual CAN (vcan0) for SIL ───────────────────────────────────────────
setup_vcan() {
    log_info "Setting up virtual CAN interface vcan0..."
    modprobe vcan 2>/dev/null || true

    if ip link show vcan0 &>/dev/null; then
        log_warn "vcan0 already exists"
    else
        ip link add dev vcan0 type vcan
        ip link set up vcan0
        log_info "vcan0 created and brought up"
    fi

    # Make persistent across reboots
    local service_file="/etc/systemd/system/vcan0.service"
    cat > "$service_file" <<'EOF'
[Unit]
Description=Virtual CAN vcan0 for ADAS SIL
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/modprobe vcan
ExecStart=/sbin/ip link add dev vcan0 type vcan
ExecStart=/sbin/ip link set up vcan0
ExecStop=/sbin/ip link del vcan0

[Install]
WantedBy=multi-user.target
EOF
    systemctl enable vcan0.service 2>/dev/null || true
    log_info "vcan0 service installed"
}

# ── 7. Kernel parameters (real-time tuning) ───────────────────────────────────
tune_kernel_params() {
    log_info "Tuning kernel parameters for real-time..."
    sysctl -w kernel.sched_rt_runtime_us=-1   # No RT throttling
    sysctl -w kernel.sched_rt_period_us=1000000
    sysctl -w vm.swappiness=0                  # Avoid swap during RT
    sysctl -w kernel.perf_event_paranoid=0     # Allow perf profiling

    # Persist
    cat >> /etc/sysctl.d/99-adas-rt.conf <<'EOF'
kernel.sched_rt_runtime_us = -1
kernel.sched_rt_period_us  = 1000000
vm.swappiness              = 0
EOF
    log_info "Kernel params tuned"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    require_root
    log_info "======= ADAS Real-Time Linux Setup ======="
    check_preempt_rt
    configure_isolcpus
    set_performance_governor
    configure_irq_affinity
    configure_rt_limits
    setup_vcan
    tune_kernel_params
    log_info "======= Setup Complete ======="
    log_info "Build with: bazel build //src:adas_rt --config=rt"
    log_info "Run  with:  sudo ./bazel-bin/src/adas_rt"
}

main "$@"
