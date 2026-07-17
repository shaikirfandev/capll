# Protocol Knowledge — SIP, Diameter, TCP/IP, GTP, HTTP/HTTP2

This module captures the essential protocol knowledge from the job description and provides hands-on labs, troubleshooting tips, and test ideas to add to the repository.

Audience: Test engineers and network engineers validating telecommunications stacks and embedded/networked firmware.

Duration: 3–5 days for an intensive deep-dive, or 2–3 weeks part-time.

Sections

1. SIP (Session Initiation Protocol)
2. Diameter
3. TCP/IP fundamentals
4. GTP (GTP-C, GTP-U)
5. HTTP/HTTP2 and REST/gRPC basics
6. Labs and Exercises
7. Test Case Ideas and Automation
8. Tools and References


## 1. SIP (Session Initiation Protocol)

Overview:
- SIP is a signaling protocol for establishing, modifying, and terminating multimedia sessions (VoIP).
- Messages: `INVITE`, `ACK`, `BYE`, `REGISTER`, `OPTIONS`, `CANCEL`, `REFER`.
- Responses: 1xx provisional, 2xx success, 3xx redirection, 4xx client error, 5xx server error, 6xx global failure.
- Key headers: `From`, `To`, `Call-ID`, `CSeq`, `Via`, `Contact`, `Route`, `Record-Route`.

Troubleshooting:
- Common issues: 401/407 authentication, 403 forbidden, 408 timeout, NAT traversal (RTP)
- Use `Wireshark` with SIP and RTP filters: `sip` and `rtp`
- Examine `Via` and `Contact` headers for routing
- Check SDP (session description) for media codecs and ports

Scapy example (simple SIP REGISTER stub):

```python
from scapy.all import *

sip = (
    "REGISTER sip:example.com SIP/2.0\r\n"
    "Via: SIP/2.0/UDP 192.0.2.1:5060;branch=z9hG4bK776asdhds\r\n"
    "Max-Forwards: 70\r\n"
    "From: <sip:alice@example.com>;tag=1928301774\r\n"
    "To: <sip:alice@example.com>\r\n"
    "Call-ID: a84b4c76e66710\r\n"
    "CSeq: 314159 REGISTER\r\n"
    "Contact: <sip:alice@192.0.2.1>\r\n"
    "Content-Length: 0\r\n\r\n"
)

send(IP(dst="198.51.100.10")/UDP(sport=5060,dport=5060)/Raw(load=sip))
```

Lab:
- Deploy Kamailio or OpenSIPS and register a softphone (Linphone)
- Capture SIP registration and call setup traces


## 2. Diameter

Overview:
- Diameter is an AAA (Authentication, Authorization, Accounting) protocol used in LTE/5G networks for policy and charging.
- Message types: `AA-Request`/`AA-Answer`, `Credit-Control-Request`/`Answer`.
- Transport: TCP/SCTP, usually with TLS for security.

Troubleshooting:
- Check AVPs (Attribute-Value Pairs) in Diameter messages
- Use `Wireshark` builtin dissector for `diameter`

Lab:
- Set up a simple Diameter test server (e.g., `freeDiameter`) and exchange basic AVPs


## 3. TCP/IP Fundamentals

Overview:
- IP addressing, subnetting, routing, ARP
- TCP three-way handshake, windowing, retransmissions
- UDP semantics and implications for RTP/GTP

Troubleshooting:
- Use `tcpdump`/`tshark` to capture and analyze packets
- Check for retransmissions, duplicate ACKs, RSTs
- Verify routing and NAT rules

Commands:

```bash
# Capture SIP traffic
sudo tcpdump -i any -w sip_capture.pcap port 5060

# Capture GTP-U (UDP 2152)
sudo tcpdump -i any -w gtp.pcap udp port 2152

# Use tshark to read pcap with protocol filters
tshark -r sip_capture.pcap -Y sip -V
```


## 4. GTP (GTP-C, GTP-U)

Overview:
- GTP is used in 3G/4G/5G for tunneling user plane and control plane traffic between EPC/5GC elements.
- `GTP-C` (control plane) typically on UDP port 2123; `GTP-U` (user plane) typically on UDP port 2152.
- TEID (Tunnel Endpoint Identifier) identifies dedicated tunnels for user traffic.

Troubleshooting:
- Inspect inner IP headers in GTP-U to validate user plane traffic
- Monitor sequence numbers and TEID mappings for session correctness

Lab:
- Run Open5GS or free5GC and trace GTP-U tunnels while a UE performs data transfer


## 5. HTTP/HTTP2 and REST/gRPC basics

Overview:
- RESTful APIs are used extensively in 5G SBA (service-based architecture)
- HTTP/2 and gRPC are common for NF-to-NF communication in modern 5G cores
- OpenAPI/Swagger for API contract definitions and testing

Troubleshooting:
- Use `curl` or Postman to exercise REST endpoints
- Check JSON schema compliance using `jsonschema` or `schemathesis`

Example:

```bash
curl -X GET "http://localhost:8000/nrf/v1/status" -H "Accept: application/json"
```


## 6. Labs and Exercises

1. SIP Registration and Calling Lab
   - Deploy Kamailio/OpenSIPS and FreeSWITCH
   - Register UA and make a call, capture and analyze SIP/RTP traces
2. Diameter AVP Exchange
   - Deploy `freeDiameter` and send a basic CCR/CCA (Credit Control Request/Answer)
3. GTP Tunnel Validation
   - Deploy Open5GS, perform data session, capture GTP-U and inspect inner IPs
4. REST/gRPC API Tests
   - Run `schemathesis` against a sample OpenAPI spec
5. Fault Injection
   - Drop/modify SIP messages mid-call and observe behavior
   - Inject GTP TEID mismatch and observe session failure


## 7. Test Case Ideas and Automation

- `PROTOCOL_SIP_001`: SIP REGISTER success
- `PROTOCOL_SIP_002`: SIP INVITE successful media flow (RTP packets seen)
- `PROTOCOL_SIP_003`: REGISTER with wrong credentials results in 401
- `PROTOCOL_GTP_001`: GTP-U packet forwarding with correct inner IPs
- `PROTOCOL_DIAM_001`: Diameter CCR/CCA flow and AVP verification
- `PROTOCOL_HTTP_001`: NF REST endpoint returns 200 and schema-valid JSON

Automation notes:
- Use `scapy` for packet crafting and verifying low-level behavior
- Use `pytest` for orchestration and assertions
- Integrate Robot Framework for higher-level acceptance tests


## 8. Tools and References

- Wireshark/Tshark
- Scapy
- tcpdump
- Kamailio / OpenSIPS / FreeSWITCH
- Open5GS / free5GC
- freeDiameter
- Postman / Newman
- Schemathesis for OpenAPI testing

References:
- RFC 3261 (SIP)
- 3GPP TS 29.274 (GTP)
- RFC 6733 (Diameter)
- HTTP/2 RFC 7540


## Adding to the Repo

- Create tests under `tests/telecom/` for each protocol test case
- Add `telecom/requirements.txt` (already added) and CI steps to run `pytest tests/telecom`
- Feed protocol-specific logs (pcap/json) into the RCA engine for pattern matching

File location: `docs/telecom_network/PROTOCOL_KNOWLEDGE.md`
