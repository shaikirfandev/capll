#!/usr/bin/env python3
"""
UDS Security Fuzzer — Automotive Cybersecurity Lab Tool

Tests UDS services for security vulnerabilities:
  - Security Access brute force / lockout policy
  - Service boundary testing (unauthorized service access)
  - DID enumeration (RDBI sweep)
  - Session transition mapping
  - Seed entropy analysis

Usage:
  python3 uds_fuzzer.py --channel vcan0 --tx 0x7E0 --rx 0x7E8 --mode all
  python3 uds_fuzzer.py --channel vcan0 --tx 0x7E0 --rx 0x7E8 --mode seed_entropy

Requirements:
  pip install python-can udsoncan can-isotp

EDUCATIONAL PURPOSE ONLY — DO NOT USE ON PRODUCTION VEHICLES
"""
import can
import isotp
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
import udsoncan.services as services
import time
import argparse
import sys
import statistics
import math
from typing import Optional, List, Tuple

# ─── UDS SESSION MANAGER ─────────────────────────────────────────────────────

class UDSFuzzer:
    def __init__(self, channel: str, tx_id: int, rx_id: int, bustype: str = "socketcan"):
        self.channel = channel
        self.tx_id = tx_id
        self.rx_id = rx_id
        self.bustype = bustype
        self._bus = None
        self._stack = None
        self._conn = None
        self.results = []

    def __enter__(self):
        self._bus = can.interface.Bus(self.channel, bustype=self.bustype)
        self._stack = isotp.CanStack(
            bus=self._bus,
            address=isotp.Address(
                isotp.AddressingMode.Normal_11bits,
                txid=self.tx_id,
                rxid=self.rx_id
            )
        )
        self._conn = PythonIsoTpConnection(self._stack)
        return self

    def __exit__(self, *args):
        if self._bus:
            self._bus.shutdown()

    def _log(self, level: str, msg: str):
        ts = time.strftime("%H:%M:%S")
        symbols = {"INFO": "[*]", "PASS": "[+]", "FAIL": "[-]", "WARN": "[!]", "CRIT": "[!!!]"}
        print(f"{ts} {symbols.get(level, '[?]')} {msg}")

    def _record(self, test: str, result: str, detail: str = ""):
        self.results.append({"test": test, "result": result, "detail": detail})
        symbol = "PASS" if result == "PASS" else "FAIL" if result == "FAIL" else "INFO"
        self._log(symbol, f"{test}: {result} {detail}")

    # ─── TEST 1: SESSION MAPPING ─────────────────────────────────────────────

    def test_session_transitions(self):
        """Map which sessions are accessible and from where"""
        self._log("INFO", "=== Test: Session Transition Mapping ===")

        sessions = {
            0x01: "Default",
            0x02: "Programming",
            0x03: "Extended",
            0x04: "SafetySystem",
        }

        with udsoncan.Client(self._conn, request_timeout=2) as client:
            # Test: can we reach Programming directly from Default?
            try:
                client.change_session(services.DiagnosticSessionControl.Session.defaultSession)
                time.sleep(0.1)
                client.change_session(0x02)  # Programming
                self._record(
                    "Direct_Programming_Session",
                    "FAIL",
                    "Programming session accessible from Default (should require Extended first)"
                )
            except udsoncan.exceptions.NegativeResponseException as e:
                self._record(
                    "Direct_Programming_Session",
                    "PASS",
                    f"Correctly rejected (NRC 0x{e.response.code:02X})"
                )
            except Exception as e:
                self._record("Direct_Programming_Session", "INFO", f"Error: {e}")

            # Test: Extended → Programming (should work)
            try:
                client.change_session(0x03)  # Extended
                time.sleep(0.1)
                client.change_session(0x02)  # Programming
                self._record(
                    "Extended_to_Programming",
                    "INFO",
                    "Extended → Programming transition successful (expected behavior)"
                )
                # Return to default
                client.change_session(0x01)
            except Exception as e:
                self._record("Extended_to_Programming", "INFO", f"Result: {e}")

    # ─── TEST 2: SECURITY ACCESS LOCKOUT ─────────────────────────────────────

    def test_security_access_lockout(self, level: int = 0x01, max_attempts: int = 15):
        """Test lockout policy after wrong key attempts"""
        self._log("INFO", "=== Test: Security Access Lockout Policy ===")

        with udsoncan.Client(self._conn, request_timeout=3) as client:
            # Enter extended session
            try:
                client.change_session(0x03)
            except Exception as e:
                self._log("WARN", f"Could not enter extended session: {e}")
                return

            attempts = 0
            lockout_after = None
            lockout_start = None

            for attempt in range(1, max_attempts + 1):
                attempts += 1
                try:
                    # Request seed
                    result = client.request_seed(level)
                    seed = int.from_bytes(result.service_data.security_seed, 'big')
                    seed_len = len(result.service_data.security_seed)

                    # Send WRONG key (XOR seed with 0xFF... — deliberately wrong)
                    wrong_key = bytes(b ^ 0xFF for b in result.service_data.security_seed)
                    client.send_key(level + 1, wrong_key)

                    self._record(
                        f"Security_Access_Attempt_{attempt}",
                        "FAIL",
                        f"Wrong key accepted! Seed=0x{seed:0{seed_len*2}X} Key={wrong_key.hex()}"
                    )
                    # Key accepted with wrong value — critical finding
                    break

                except udsoncan.exceptions.NegativeResponseException as e:
                    nrc = e.response.code
                    if nrc == 0x35:  # invalidKey
                        self._log("INFO", f"  Attempt {attempt}: Wrong key rejected (NRC 0x35) — expected")
                    elif nrc == 0x36:  # exceededNumberOfAttempts
                        lockout_after = attempt
                        lockout_start = time.time()
                        self._log("INFO", f"  Attempt {attempt}: LOCKOUT triggered (NRC 0x36)")
                        break
                    elif nrc == 0x37:  # requiredTimeDelayNotExpired
                        lockout_after = attempt
                        lockout_start = time.time()
                        self._log("INFO", f"  Attempt {attempt}: Delay not expired (NRC 0x37)")
                        break
                    elif nrc == 0x24:  # requestSequenceError
                        self._log("WARN", f"  Attempt {attempt}: Sequence error — check session")
                        break
                    else:
                        self._log("WARN", f"  Attempt {attempt}: Unexpected NRC 0x{nrc:02X}")
                except Exception as e:
                    self._log("WARN", f"  Attempt {attempt}: Exception: {e}")
                    break

            # Evaluate results
            if lockout_after:
                self._record(
                    "Lockout_Policy",
                    "PASS" if lockout_after <= 3 else "FAIL",
                    f"Locked after {lockout_after} attempts (target: ≤3)"
                )
                # Measure lockout duration
                if lockout_start:
                    self._measure_lockout_duration(client, level, lockout_start)
            else:
                self._record("Lockout_Policy", "FAIL", f"No lockout after {attempts} wrong attempts")

    def _measure_lockout_duration(self, client, level: int, start_time: float):
        """Measure how long the lockout lasts"""
        self._log("INFO", "  Measuring lockout duration...")
        for elapsed in range(1, 120):
            time.sleep(1)
            try:
                client.request_seed(level)
                duration = time.time() - start_time
                self._record(
                    "Lockout_Duration",
                    "PASS" if duration >= 10.0 else "FAIL",
                    f"Lockout lasted {duration:.1f}s (target: ≥10s)"
                )
                return
            except udsoncan.exceptions.NegativeResponseException as e:
                if e.response.code not in (0x36, 0x37):
                    break
            except Exception:
                break
        self._record("Lockout_Duration", "INFO", "Lockout > 120s (measurement timeout)")

    # ─── TEST 3: SEED ENTROPY ANALYSIS ───────────────────────────────────────

    def test_seed_entropy(self, level: int = 0x01, sample_size: int = 50):
        """Analyze seed randomness — low entropy = predictable = brute-force risk"""
        self._log("INFO", f"=== Test: Seed Entropy Analysis (n={sample_size}) ===")

        seeds = []
        with udsoncan.Client(self._conn, request_timeout=3) as client:
            try:
                client.change_session(0x03)
            except Exception:
                pass

            for i in range(sample_size):
                try:
                    result = client.request_seed(level)
                    seed_bytes = result.service_data.security_seed
                    seed_int = int.from_bytes(seed_bytes, 'big')
                    seeds.append(seed_int)
                    # Reset security state between requests
                    try:
                        client.change_session(0x01)
                        client.change_session(0x03)
                    except Exception:
                        pass
                    time.sleep(0.05)
                except Exception as e:
                    self._log("WARN", f"  Seed request {i+1} failed: {e}")

        if len(seeds) < 10:
            self._record("Seed_Entropy", "INFO", f"Too few samples ({len(seeds)}) for analysis")
            return

        # Basic uniqueness check
        unique_seeds = len(set(seeds))
        uniqueness_pct = (unique_seeds / len(seeds)) * 100

        self._record(
            "Seed_Uniqueness",
            "PASS" if uniqueness_pct > 95 else "FAIL",
            f"{unique_seeds}/{len(seeds)} unique ({uniqueness_pct:.1f}%)"
        )

        # Check for sequential counters
        diffs = [seeds[i+1] - seeds[i] for i in range(len(seeds)-1)]
        if len(set(diffs)) == 1:
            self._record(
                "Seed_Not_Sequential",
                "FAIL",
                f"Seed increments by constant {diffs[0]} — PREDICTABLE!"
            )
        else:
            self._record("Seed_Not_Sequential", "PASS", "Seeds are not sequential")

        # Shannon entropy of seed byte distribution
        all_bytes = []
        for s in seeds:
            seed_bytes = s.to_bytes((s.bit_length() + 7) // 8 or 1, 'big')
            all_bytes.extend(seed_bytes)

        freq = {}
        for b in all_bytes:
            freq[b] = freq.get(b, 0) + 1
        entropy = -sum((c/len(all_bytes)) * math.log2(c/len(all_bytes))
                       for c in freq.values())

        self._record(
            "Seed_Shannon_Entropy",
            "PASS" if entropy > 6.0 else "FAIL",
            f"Entropy={entropy:.2f} bits/byte (target: >6.0 for strong randomness)"
        )

    # ─── TEST 4: DID ENUMERATION ──────────────────────────────────────────────

    def test_did_enumeration(self, did_range: tuple = (0xF100, 0xF1FF)):
        """Enumerate accessible DIDs (RDBI sweep)"""
        self._log("INFO", f"=== Test: DID Enumeration 0x{did_range[0]:04X}–0x{did_range[1]:04X} ===")

        accessible = []
        with udsoncan.Client(self._conn, request_timeout=1) as client:
            try:
                client.change_session(0x03)
            except Exception:
                pass

            for did in range(did_range[0], did_range[1] + 1):
                try:
                    resp = client.read_data_by_identifier(did)
                    data = resp.service_data.values.get(did, b"")
                    accessible.append((did, data))
                    self._log("INFO", f"  DID 0x{did:04X}: {data.hex() if isinstance(data, bytes) else data}")
                except udsoncan.exceptions.NegativeResponseException as e:
                    if e.response.code != 0x31:  # requestOutOfRange = normal
                        self._log("WARN", f"  DID 0x{did:04X}: NRC 0x{e.response.code:02X}")
                except Exception:
                    pass

        self._record(
            "DID_Enumeration",
            "INFO",
            f"Found {len(accessible)} accessible DIDs in range 0x{did_range[0]:04X}–0x{did_range[1]:04X}"
        )

    # ─── REPORT ──────────────────────────────────────────────────────────────

    def print_report(self):
        print("\n" + "=" * 80)
        print("UDS SECURITY FUZZER — TEST REPORT")
        print("=" * 80)
        pass_count = sum(1 for r in self.results if r["result"] == "PASS")
        fail_count = sum(1 for r in self.results if r["result"] == "FAIL")
        info_count = sum(1 for r in self.results if r["result"] == "INFO")

        print(f"\nRESULTS: {pass_count} PASS, {fail_count} FAIL, {info_count} INFO")
        print()

        if fail_count > 0:
            print("FAILURES (Action Required):")
            for r in self.results:
                if r["result"] == "FAIL":
                    print(f"  [FAIL] {r['test']}: {r['detail']}")

        print("\nFULL RESULTS:")
        for r in self.results:
            symbol = "✓" if r["result"] == "PASS" else "✗" if r["result"] == "FAIL" else "i"
            print(f"  [{symbol}] {r['test']}: {r['result']} — {r['detail']}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="UDS Security Fuzzer")
    p.add_argument("--channel", default="vcan0", help="CAN interface")
    p.add_argument("--bustype", default="socketcan",
                   choices=["socketcan", "pcan", "vector", "kvaser"])
    p.add_argument("--tx", default="0x7E0", help="Tester TX ID (default: 0x7E0)")
    p.add_argument("--rx", default="0x7E8", help="ECU RX ID (default: 0x7E8)")
    p.add_argument("--mode", default="all",
                   choices=["all", "sessions", "lockout", "seed_entropy", "did_enum"],
                   help="Test mode")
    p.add_argument("--level", type=int, default=0x01, help="Security access level (default: 1)")
    p.add_argument("--seed-samples", type=int, default=50, help="Seed entropy samples")
    return p.parse_args()


def main():
    args = parse_args()
    tx_id = int(args.tx, 16)
    rx_id = int(args.rx, 16)

    print(f"[UDS Fuzzer] Target: TX=0x{tx_id:03X} RX=0x{rx_id:03X} on {args.channel}")
    print("[UDS Fuzzer] FOR EDUCATIONAL USE ON TEST BENCH ONLY")
    print("─" * 80)

    with UDSFuzzer(args.channel, tx_id, rx_id, args.bustype) as fuzzer:
        if args.mode in ("all", "sessions"):
            fuzzer.test_session_transitions()
        if args.mode in ("all", "lockout"):
            fuzzer.test_security_access_lockout(level=args.level)
        if args.mode in ("all", "seed_entropy"):
            fuzzer.test_seed_entropy(level=args.level, sample_size=args.seed_samples)
        if args.mode in ("all", "did_enum"):
            fuzzer.test_did_enumeration()

        fuzzer.print_report()


if __name__ == "__main__":
    main()
