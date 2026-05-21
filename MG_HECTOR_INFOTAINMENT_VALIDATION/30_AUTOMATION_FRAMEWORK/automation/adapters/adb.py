from __future__ import annotations

import subprocess
from pathlib import Path


class AdbAdapter:
    def __init__(self, serial: str = "") -> None:
        self.serial = serial

    def _cmd(self, *args: str) -> list[str]:
        base = ["adb"]
        if self.serial:
            base += ["-s", self.serial]
        return base + list(args)

    def run(self, *args: str, timeout: int = 20) -> str:
        try:
            return subprocess.check_output(
                self._cmd(*args),
                text=True,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
        except Exception as exc:
            return f"ADB_DRY_OR_UNAVAILABLE: {exc}"

    def collect_logcat(self, output: Path, seconds: int = 5) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        text = self.run("logcat", "-d", "-v", "threadtime", timeout=max(10, seconds))
        output.write_text(text, encoding="utf-8", errors="ignore")
        return output

    def build_fingerprint(self) -> str:
        return self.run("shell", "getprop", "ro.build.fingerprint").strip()

