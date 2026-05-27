#!/usr/bin/env python3
"""
Firmware Security Analyzer — Automotive Cybersecurity Lab Tool

Performs static analysis on ECU firmware binaries:
  - Shannon entropy analysis (detect encrypted/compressed regions)
  - File format detection (ELF, Intel HEX, SREC, raw binary)
  - Security-relevant string extraction (keys, URLs, credentials, UDS, CVEs)
  - Binary structure mapping (code / data / high-entropy regions)
  - Printable string extraction with classification

Usage:
  python3 firmware_analyzer.py firmware.bin
  python3 firmware_analyzer.py firmware.elf --block 256 --strings-only
  python3 firmware_analyzer.py firmware.hex --format ihex --output report.txt

Requirements:
  pip install colorama
  (No binary dependencies — pure Python, no binwalk required)

Author: Automotive Cybersecurity Lab
"""
import sys
import os
import math
import struct
import argparse
import re
import json
from typing import List, Tuple, Dict, Optional
from collections import Counter

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

# ─── COLOR HELPERS ───────────────────────────────────────────────────────────

def red(s): return f"{Fore.RED}{s}{Style.RESET_ALL}" if HAS_COLOR else s
def green(s): return f"{Fore.GREEN}{s}{Style.RESET_ALL}" if HAS_COLOR else s
def yellow(s): return f"{Fore.YELLOW}{s}{Style.RESET_ALL}" if HAS_COLOR else s
def cyan(s): return f"{Fore.CYAN}{s}{Style.RESET_ALL}" if HAS_COLOR else s

# ─── SECURITY PATTERNS ───────────────────────────────────────────────────────

SECURITY_PATTERNS = {
    "HARDCODED_KEY": [
        r'(?i)(password|passwd|secret|apikey|api_key|token)\s*[=:]\s*["\']?[\w\-\.+/=]{8,}',
        r'(?i)(key|aes|hmac|rsa|private)\s*[=:]\s*[0-9a-fA-F]{16,}',
    ],
    "PRIVATE_KEY_PEM": [
        r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
        r'-----BEGIN CERTIFICATE-----',
    ],
    "URL_ENDPOINT": [
        r'https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}[/\w\-\.\?=&%]*',
        r'mqtt://[a-zA-Z0-9\-\.]+',
    ],
    "IP_ADDRESS": [
        r'\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b',
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    ],
    "UDS_DIAGNOSTIC": [
        r'(?i)(security.?access|seed.?key|diagnostic.?session|unlockKey)',
        r'\\x27\\x[0-9a-fA-F]{2}',  # Security Access service
    ],
    "DEBUG_STRINGS": [
        r'(?i)(debug|test.?mode|backdoor|bypass|override|skip.?check)',
        r'(?i)(factory.?mode|engineering.?mode|dev.?mode)',
    ],
    "CRYPTO_MAGIC": [
        r'(?i)(AES|RSA|ECDSA|SHA256|HMAC|CMAC|TLS)',
    ],
    "WEAK_CRYPTO": [
        r'(?i)\b(MD5|SHA1|DES|3DES|RC4|RC2)\b',
    ],
}

# ─── FILE FORMAT DETECTION ───────────────────────────────────────────────────

def detect_format(data: bytes) -> str:
    """Detect firmware file format from magic bytes"""
    if data[:4] == b'\x7fELF':
        e_type = struct.unpack_from('<H', data, 16)[0]
        types = {2: "ELF Executable", 3: "ELF Shared Library", 4: "ELF Core"}
        return f"ELF ({types.get(e_type, 'Unknown ELF type')})"
    if data[:2] in (b'MZ', b'ZM'):
        return "PE/COFF (Windows executable)"
    if data[:4] in (b'\xFE\xED\xFA\xCE', b'\xCE\xFA\xED\xFE',
                    b'\xFE\xED\xFA\xCF', b'\xCF\xFA\xED\xFE'):
        return "Mach-O Binary"
    # Intel HEX: starts with ':'
    if data[:1] == b':' and data[1:3].isdigit():
        return "Intel HEX (.hex)"
    # Motorola SREC: starts with 'S'
    if data[:2] in (b'S0', b'S1', b'S2', b'S3'):
        return "Motorola SREC"
    # Compressed formats
    if data[:2] == b'\x1f\x8b':
        return "gzip compressed"
    if data[:4] == b'PK\x03\x04':
        return "ZIP/JAR archive"
    if data[:6] == b'070701' or data[:6] == b'070702':
        return "CPIO archive"
    if data[:4] == b'\x27\x05\x19\x56':
        return "U-Boot uImage"
    if data[:4] == b'\x68\x73\x71\x73':
        return "SquashFS filesystem"
    if data[:3] == b'BZh':
        return "bzip2 compressed"
    # UBI filesystem
    if data[:4] == b'UBI#':
        return "UBI Filesystem"
    return "Raw Binary"

# ─── INTEL HEX PARSER ────────────────────────────────────────────────────────

def parse_intel_hex(data: bytes) -> bytes:
    """Convert Intel HEX to raw binary"""
    raw = bytearray()
    for line in data.decode('ascii', errors='replace').splitlines():
        if not line.startswith(':'):
            continue
        byte_count = int(line[1:3], 16)
        rec_type = int(line[7:9], 16)
        if rec_type == 0x00:  # Data record
            hex_data = line[9:9 + byte_count * 2]
            raw.extend(bytes.fromhex(hex_data))
    return bytes(raw)

# ─── ENTROPY ANALYSIS ────────────────────────────────────────────────────────

def shannon_entropy(data: bytes) -> float:
    """Calculate Shannon entropy (bits per byte)"""
    if not data:
        return 0.0
    freq = Counter(data)
    length = len(data)
    return -sum((c/length) * math.log2(c/length) for c in freq.values())

def entropy_classify(e: float) -> Tuple[str, str]:
    """Return (label, color_func_name) based on entropy value"""
    if e > 7.5:
        return ("ENCRYPTED/COMPRESSED", "RED")
    elif e > 6.5:
        return ("HIGH ENTROPY (likely compressed)", "YELLOW")
    elif e > 5.0:
        return ("MODERATE (code/data)", "GREEN")
    elif e > 3.0:
        return ("LOW (text/config)", "CYAN")
    else:
        return ("VERY LOW (padding/zeroes)", "CYAN")

def analyze_entropy_blocks(data: bytes, block_size: int) -> List[Dict]:
    """Analyze entropy in fixed-size blocks"""
    blocks = []
    for offset in range(0, len(data), block_size):
        block = data[offset:offset + block_size]
        if len(block) < 16:
            continue
        e = shannon_entropy(block)
        label, color = entropy_classify(e)
        blocks.append({
            "offset": offset,
            "size": len(block),
            "entropy": e,
            "label": label
        })
    return blocks

# ─── STRING EXTRACTION ───────────────────────────────────────────────────────

def extract_printable_strings(data: bytes, min_length: int = 6) -> List[Tuple[int, str]]:
    """Extract printable ASCII strings from binary"""
    strings = []
    current = []
    start = 0

    for i, byte in enumerate(data):
        if 0x20 <= byte <= 0x7E:  # Printable ASCII range
            if not current:
                start = i
            current.append(chr(byte))
        else:
            if len(current) >= min_length:
                strings.append((start, ''.join(current)))
            current = []

    if len(current) >= min_length:
        strings.append((start, ''.join(current)))

    return strings

def classify_strings(strings: List[Tuple[int, str]]) -> Dict[str, List[Tuple[int, str]]]:
    """Classify extracted strings by security relevance"""
    classified = {category: [] for category in SECURITY_PATTERNS}
    classified["OTHER"] = []

    for offset, s in strings:
        matched = False
        for category, patterns in SECURITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, s):
                    classified[category].append((offset, s))
                    matched = True
                    break
            if matched:
                break
        if not matched:
            classified["OTHER"].append((offset, s))

    return classified

# ─── ELF SECTION PARSER ──────────────────────────────────────────────────────

def parse_elf_sections(data: bytes) -> List[Dict]:
    """Parse ELF section headers for basic info"""
    sections = []
    if data[:4] != b'\x7fELF':
        return sections

    is_64bit = data[4] == 2
    is_le = data[5] == 1

    endian = '<' if is_le else '>'

    try:
        if is_64bit:
            e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from(
                f'{endian}QHHH', data, 40
            )
            sh_fmt = f'{endian}QQQQQQIIQQ'
            sh_size = 64
        else:
            e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from(
                f'{endian}IHHH', data, 32
            )
            sh_fmt = f'{endian}IIIIIIIIII'
            sh_size = 40

        # Read string table section
        shstr_offset = e_shoff + e_shstrndx * sh_size
        if is_64bit:
            str_sh_offset, str_sh_size = struct.unpack_from(f'{endian}QQ', data, shstr_offset + 24)
        else:
            str_sh_offset, str_sh_size = struct.unpack_from(f'{endian}II', data, shstr_offset + 16)

        for i in range(e_shnum):
            sh_data = struct.unpack_from(sh_fmt, data, e_shoff + i * sh_size)
            name_idx = sh_data[0]
            if is_64bit:
                sh_offset, sh_size_bytes = sh_data[4], sh_data[5]
                sh_flags = sh_data[3]
            else:
                sh_offset, sh_size_bytes = sh_data[4], sh_data[5]
                sh_flags = sh_data[3]

            # Get name from string table
            name_start = str_sh_offset + name_idx
            name_end = data.find(b'\x00', name_start)
            name = data[name_start:name_end].decode('ascii', errors='replace') if name_end > name_start else f"<unnamed_{i}>"

            if sh_size_bytes > 0 and sh_offset > 0:
                section_data = data[sh_offset:sh_offset + sh_size_bytes]
                entropy = shannon_entropy(section_data) if section_data else 0.0
                sections.append({
                    "name": name,
                    "offset": sh_offset,
                    "size": sh_size_bytes,
                    "entropy": entropy,
                    "flags": sh_flags
                })
    except (struct.error, IndexError):
        pass

    return sections

# ─── REPORTER ────────────────────────────────────────────────────────────────

class FirmwareReport:
    def __init__(self):
        self.findings = []
        self.severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "INFO": 0}

    def add(self, severity: str, category: str, description: str, offset: int = -1):
        self.findings.append({
            "severity": severity,
            "category": category,
            "description": description,
            "offset": offset
        })
        self.severity_counts[severity] = self.severity_counts.get(severity, 0) + 1

    def print_report(self, output_file=None):
        def emit(line):
            print(line)
            if output_file:
                output_file.write(line + "\n")

        emit("=" * 80)
        emit("FIRMWARE SECURITY ANALYSIS REPORT")
        emit("=" * 80)

        # Summary
        emit(f"\nFINDINGS: CRITICAL={self.severity_counts['CRITICAL']} "
             f"HIGH={self.severity_counts['HIGH']} "
             f"MEDIUM={self.severity_counts['MEDIUM']} "
             f"INFO={self.severity_counts['INFO']}")

        for sev in ("CRITICAL", "HIGH", "MEDIUM", "INFO"):
            matching = [f for f in self.findings if f["severity"] == sev]
            if matching:
                emit(f"\n[{sev}]")
                for f in matching:
                    offset_str = f" @ 0x{f['offset']:08X}" if f['offset'] >= 0 else ""
                    emit(f"  [{f['category']}]{offset_str} {f['description']}")


# ─── MAIN ANALYZER ───────────────────────────────────────────────────────────

def analyze(filepath: str, block_size: int, strings_only: bool, output_path: Optional[str]):
    data = open(filepath, 'rb').read()
    size = len(data)

    report = FirmwareReport()
    out_file = open(output_path, 'w') if output_path else None

    def emit(line):
        print(line)
        if out_file:
            out_file.write(line + "\n")

    emit(f"\n[FIRMWARE ANALYZER] File: {filepath}")
    emit(f"[FIRMWARE ANALYZER] Size: {size:,} bytes ({size/1024:.1f} KB)")

    # Format detection
    fmt = detect_format(data)
    emit(f"[FIRMWARE ANALYZER] Format: {fmt}")
    report.add("INFO", "FILE_FORMAT", f"Detected: {fmt}")

    # Intel HEX: decode to raw
    if "Intel HEX" in fmt:
        data = parse_intel_hex(data)
        emit(f"[FIRMWARE ANALYZER] Decoded Intel HEX: {len(data):,} bytes")

    emit("")

    # ─── ENTROPY ANALYSIS ────────────────────────────────────────────────────
    if not strings_only:
        overall_entropy = shannon_entropy(data)
        label, _ = entropy_classify(overall_entropy)
        emit(f"[ENTROPY] Overall: {overall_entropy:.4f} bits/byte — {label}")

        if overall_entropy > 7.5:
            report.add("HIGH", "ENTROPY", f"High overall entropy ({overall_entropy:.2f}) — firmware may be encrypted")
        elif overall_entropy < 3.0:
            report.add("INFO", "ENTROPY", f"Low entropy ({overall_entropy:.2f}) — uncompressed/unencrypted")
        else:
            report.add("INFO", "ENTROPY", f"Entropy: {overall_entropy:.2f} ({label})")

        # Block-level entropy map
        blocks = analyze_entropy_blocks(data, block_size)
        high_entropy_blocks = [b for b in blocks if b["entropy"] > 7.5]
        low_entropy_blocks = [b for b in blocks if b["entropy"] < 2.0]

        emit(f"\n[ENTROPY MAP] Block size: {block_size} bytes | Total blocks: {len(blocks)}")
        emit(f"  High entropy blocks (>7.5): {len(high_entropy_blocks)}")
        emit(f"  Low entropy blocks (<2.0):  {len(low_entropy_blocks)}")

        if high_entropy_blocks:
            emit("\n[ENTROPY MAP] High-entropy regions (likely encrypted/compressed):")
            for b in high_entropy_blocks[:20]:  # Show first 20
                emit(f"  0x{b['offset']:08X} – 0x{b['offset']+b['size']:08X} "
                     f"({b['size']} bytes) entropy={b['entropy']:.3f}")

        # ELF section analysis
        if data[:4] == b'\x7fELF':
            sections = parse_elf_sections(data)
            if sections:
                emit(f"\n[ELF SECTIONS] Found {len(sections)} sections:")
                for sec in sections:
                    label, _ = entropy_classify(sec["entropy"])
                    emit(f"  {sec['name']:<20} offset=0x{sec['offset']:08X} "
                         f"size={sec['size']:>8,}B entropy={sec['entropy']:.3f} — {label}")
                    if sec["entropy"] > 7.5:
                        report.add("MEDIUM", "ELF_ENTROPY",
                                   f"Section {sec['name']} has high entropy ({sec['entropy']:.2f})",
                                   sec["offset"])

    emit("")

    # ─── STRING EXTRACTION ────────────────────────────────────────────────────
    all_strings = extract_printable_strings(data)
    emit(f"[STRINGS] Extracted {len(all_strings)} printable strings (min 6 chars)")

    classified = classify_strings(all_strings)

    security_categories = [c for c in SECURITY_PATTERNS if classified.get(c)]
    if security_categories:
        emit("\n[STRINGS] Security-relevant findings:")

    for category in SECURITY_PATTERNS:
        matches = classified.get(category, [])
        if not matches:
            continue

        severity = {
            "HARDCODED_KEY": "CRITICAL",
            "PRIVATE_KEY_PEM": "CRITICAL",
            "WEAK_CRYPTO": "HIGH",
            "DEBUG_STRINGS": "HIGH",
            "URL_ENDPOINT": "MEDIUM",
            "IP_ADDRESS": "MEDIUM",
            "UDS_DIAGNOSTIC": "MEDIUM",
            "CRYPTO_MAGIC": "INFO",
        }.get(category, "INFO")

        emit(f"\n  [{severity}] {category} — {len(matches)} matches:")
        for offset, s in matches[:15]:  # Show first 15 per category
            emit(f"    0x{offset:08X}: {s[:120]}")
            report.add(severity, category, s[:120], offset)

        if len(matches) > 15:
            emit(f"    ... and {len(matches)-15} more")

    # Print final report
    emit("")
    report.print_report(out_file)

    if out_file:
        out_file.close()
        print(f"\n[SAVED] Report written to {output_path}")


# ─── ARGUMENT PARSING ────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Firmware Security Analyzer")
    p.add_argument("firmware", help="Firmware file path (.bin, .elf, .hex, .srec)")
    p.add_argument("--block", type=int, default=512,
                   help="Entropy analysis block size in bytes (default: 512)")
    p.add_argument("--strings-only", action="store_true",
                   help="Only perform string extraction (skip entropy analysis)")
    p.add_argument("--format", choices=["auto", "raw", "ihex", "srec"],
                   default="auto", help="Input format (default: auto-detect)")
    p.add_argument("--output", help="Save report to file")
    p.add_argument("--min-string", type=int, default=6,
                   help="Minimum printable string length (default: 6)")
    return p.parse_args()


def main():
    args = parse_args()
    if not os.path.isfile(args.firmware):
        print(f"[ERROR] File not found: {args.firmware}")
        sys.exit(1)
    analyze(args.firmware, block_size=args.block,
            strings_only=args.strings_only, output_path=args.output)


if __name__ == "__main__":
    main()
