"""
Root Cause Analysis Engine
Analyzes firmware logs and identifies failure signatures
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FailureSignature:
    """Failure signature pattern"""
    name: str
    keywords: List[str]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    likely_cause: str
    recommended_action: str


class RCAEngine:
    """Root Cause Analysis Engine"""
    
    # Known failure signatures
    SIGNATURES = [
        FailureSignature(
            name="Memory Training Failure",
            keywords=["memory", "training", "failed", "DDR"],
            severity="CRITICAL",
            likely_cause="Memory initialization error, bad memory module, or training algorithm issue",
            recommended_action="Check memory module compatibility, run memory diagnostics, verify BIOS settings"
        ),
        FailureSignature(
            name="PCIe Link Failure",
            keywords=["PCIe", "link", "failed", "enumeration", "training"],
            severity="HIGH",
            likely_cause="PCIe device initialization error, bad link quality, or signal integrity issue",
            recommended_action="Check PCIe device connections, run PCIe link training tests, check signal integrity"
        ),
        FailureSignature(
            name="Security Failure",
            keywords=["security", "certificate", "signature", "validation", "failed"],
            severity="CRITICAL",
            likely_cause="Invalid certificate, tampered firmware, or security policy violation",
            recommended_action="Verify firmware integrity, check certificate validity, review security logs"
        ),
        FailureSignature(
            name="USB Enumeration Failure",
            keywords=["USB", "enumeration", "failed", "device"],
            severity="MEDIUM",
            likely_cause="USB device not responding, USB hub issue, or controller failure",
            recommended_action="Disconnect and reconnect USB devices, check USB hub power, verify USB controller"
        ),
        FailureSignature(
            name="Temperature Thermal Throttling",
            keywords=["temperature", "critical", "thermal", "overheat"],
            severity="HIGH",
            likely_cause="System overheating, fan failure, or thermal paste degradation",
            recommended_action="Check system cooling, verify fan operation, clean heat sinks, replace thermal paste"
        ),
        FailureSignature(
            name="Firmware Corruption",
            keywords=["firmware", "corrupted", "CRC", "checksum", "corruption"],
            severity="CRITICAL",
            likely_cause="Firmware flash corruption, bad flash memory, or power loss during update",
            recommended_action="Restore firmware from backup, verify flash memory health, retry firmware update"
        ),
        FailureSignature(
            name="Power State Transition Failure",
            keywords=["power", "state", "transition", "S0", "S3", "S5", "failed"],
            severity="MEDIUM",
            likely_cause="Power sequencing issue, firmware bug, or hardware power control issue",
            recommended_action="Check power sequencing, verify firmware logic, test power supply"
        ),
        FailureSignature(
            name="Boot Timeout",
            keywords=["timeout", "boot", "deadlock", "hang"],
            severity="HIGH",
            likely_cause="Boot sequence deadlock, infinite loop, or missing device initialization",
            recommended_action="Check boot sequence logs, enable verbose logging, run selective boot tests"
        ),
    ]
    
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.logs = []
        self.analysis_results = {}
        
        if self.log_file.exists():
            self.load_logs()
    
    def load_logs(self):
        """Load logs from file"""
        try:
            with open(self.log_file, 'r') as f:
                content = f.read()
                
            # Try to parse as JSON first
            lines = content.strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        self.logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        self.logs.append({"message": line, "type": "text"})
        except Exception as e:
            print(f"Error loading logs: {e}")
    
    def extract_keywords(self, log_entry: Dict[str, Any]) -> List[str]:
        """Extract keywords from log entry"""
        keywords = []
        text = str(log_entry).lower()
        
        # Extract key terms
        terms = re.findall(r'\b[a-z_]+\b', text)
        keywords.extend(terms)
        
        return keywords
    
    def find_failures(self) -> List[Dict[str, Any]]:
        """Find failures in logs"""
        failures = []
        
        for i, log_entry in enumerate(self.logs):
            log_text = str(log_entry).lower()
            
            # Look for error indicators
            if any(word in log_text for word in ["error", "failed", "failure", "critical", "fatal"]):
                failures.append({
                    "index": i,
                    "log": log_entry,
                    "severity": self.estimate_severity(log_text)
                })
        
        return failures
    
    def estimate_severity(self, log_text: str) -> str:
        """Estimate failure severity"""
        if "critical" in log_text or "fatal" in log_text:
            return "CRITICAL"
        elif "error" in log_text:
            return "HIGH"
        elif "warning" in log_text:
            return "MEDIUM"
        else:
            return "LOW"
    
    def match_signatures(self, keywords: List[str]) -> List[FailureSignature]:
        """Match failure signatures"""
        matches = []
        
        for signature in self.SIGNATURES:
            if any(kw in keywords for kw in signature.keywords):
                matches.append(signature)
        
        return matches
    
    def analyze(self) -> Dict[str, Any]:
        """Perform RCA analysis"""
        failures = self.find_failures()
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_logs": len(self.logs),
            "failures_found": len(failures),
            "detailed_analysis": []
        }
        
        for failure in failures:
            keywords = self.extract_keywords(failure["log"])
            signatures = self.match_signatures(keywords)
            
            failure_analysis = {
                "index": failure["index"],
                "log_entry": failure["log"],
                "severity": failure["severity"],
                "matching_signatures": [
                    {
                        "name": sig.name,
                        "severity": sig.severity,
                        "likely_cause": sig.likely_cause,
                        "recommended_action": sig.recommended_action
                    }
                    for sig in signatures
                ]
            }
            
            analysis["detailed_analysis"].append(failure_analysis)
        
        return analysis
    
    def generate_report(self) -> str:
        """Generate RCA report"""
        analysis = self.analyze()
        
        report = "="*70 + "\n"
        report += "ROOT CAUSE ANALYSIS REPORT\n"
        report += "="*70 + "\n\n"
        
        report += f"Analysis Time: {analysis['timestamp']}\n"
        report += f"Total Logs: {analysis['total_logs']}\n"
        report += f"Failures Found: {analysis['failures_found']}\n\n"
        
        if analysis["detailed_analysis"]:
            report += "Detailed Failures:\n"
            report += "-"*70 + "\n\n"
            
            for i, failure in enumerate(analysis["detailed_analysis"], 1):
                report += f"Failure #{i}\n"
                report += f"  Log Index: {failure['index']}\n"
                report += f"  Severity: {failure['severity']}\n"
                
                if failure["matching_signatures"]:
                    report += "  Matching Signatures:\n"
                    for sig in failure["matching_signatures"]:
                        report += f"    - {sig['name']}\n"
                        report += f"      Likely Cause: {sig['likely_cause']}\n"
                        report += f"      Recommended Action: {sig['recommended_action']}\n"
                else:
                    report += "  No matching signatures found\n"
                
                report += "\n"
        else:
            report += "No failures detected in logs\n"
        
        report += "="*70 + "\n"
        
        return report
    
    def save_report(self, output_file: str = "rca_report.txt"):
        """Save report to file"""
        report = self.generate_report()
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        return output_file


def main():
    """Main RCA analysis"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rca_engine.py <log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    engine = RCAEngine(log_file)
    
    report = engine.generate_report()
    print(report)
    
    report_file = engine.save_report()
    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    main()
