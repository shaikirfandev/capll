# Linux IVI Debugging Cheatsheet

```bash
ps -A
top -H
dmesg -T
journalctl -b
systemctl --failed
ip addr
ss -tulpn
df -h
mount
```

Use process, service, kernel, filesystem and network evidence to separate app-layer problems from platform and driver problems.
