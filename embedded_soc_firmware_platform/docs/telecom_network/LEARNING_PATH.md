# Telecom & Network Core — Learning Path

This learning path converts the job description competencies into a structured training program for engineers seeking expertise in Mobile Core Networks, IMS, VoLTE/5G SBA, automation, protocols, advanced networking, and cloud deployment.

Audience: Firmware, validation, and network engineers aiming to work on Mobile Core/IMS and post-silicon networked platforms.

Duration: 8–10 weeks (full-time) or 3–4 months (part-time). The program is modular — pick relevant modules.

Prerequisites

- Solid programming skills (Python recommended)
- Working knowledge of Linux (networking, packages, services)
- Basic familiarity with IP networking and TCP/IP
- Optional: prior exposure to telephony or embedded firmware

Learning Goals

- Understand mobile core architectures (EPC and 5GC) and IMS
- Implement and test SIP/VoLTE call flows and core interactions
- Automate test cases using Python and Robot Framework
- Validate NF REST APIs and service-based interfaces
- Gain familiarity with GTP, Diameter, and SIP troubleshooting
- Deploy and test CNFs on Kubernetes and VMs on OpenStack
- Instrument and analyze logs to drive RCA and test coverage

Program Outline

Module 0 — Setup & Tooling (2 days)
- Install required tools and emulators: Docker, Docker Compose, Python 3.9+, Git, Wireshark
- Optional: Virtualization: libvirt, Minikube or a k8s cluster
- Install Python dependencies and Robot Framework

Quick commands

```bash
# Create a Python venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install requests scapy pytest robotframework
```

Module 1 — Mobile Core Fundamentals (EPC & 5GC) (3 days)
- EPC components: MME, HSS, SGW, PGW — roles and interfaces (S1, S5, S11)
- 5G Core components: AMF, SMF, UPF, NRF — SBA concepts
- Control plane vs data plane separation
- GTP basics: GTP-C and GTP-U flows

Hands-on:
- Deploy Open5GS (container or VM)
- Inspect MME/AMF logs, simulate UE attach and session establishment

Module 2 — IMS & SIP (3 days)
- SIP: REGISTER, INVITE, 200 OK, ACK, BYE, REFER
- IMS architecture: P-CSCF, I-CSCF, S-CSCF, HSS
- RTP media flow and NAT traversal

Hands-on:
- Install Kamailio or OpenSIPS + Asterisk/FreeSWITCH
- Run simple SIP registration and call using softphones (Linphone)
- Capture and analyze SIP traces with Wireshark

Module 3 — VoLTE and 5G SBA (2 days)
- VoLTE call flow with IMS components
- 5G Service Based Architecture: NF discovery, RESTful APIs between NFs
- Stateless vs stateful NF design and scaling patterns

Hands-on:
- Simulate a basic VoLTE call using Open5GS + IMS stack
- Inspect REST interactions in 5GC emulators (free5GC)

Module 4 — Protocol Deep Dives (4 days)
- SIP advanced topics: forking, proxies, headers, registration challenges
- Diameter overview: AA/AC flows, credit control, policy
- GTP tunneling, sequence numbers, and troubleshooting
- HTTP/HTTP2 and gRPC basics for NF APIs

Exercises:
- Write a Scapy-based script to craft custom SIP messages
- Capture and decode GTP-U packets, extract TEID and inner IP

Module 5 — Programming & Automation (1 week)
- Python: scripting, asyncio, requests, pytest integration
- Robot Framework: keyword-driven tests, libraries for REST and SSH
- REST API testing: OpenAPI/Swagger, contract tests
- CI/CD: GitHub Actions / GitLab pipelines for test automation

Deliverables:
- CI pipeline to run smoke tests on each push
- Robot test suite for acceptance tests

Example GitHub Actions snippet

```yaml
name: telecom-tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9
      - name: Install deps
        run: |
          python -m pip install -r telecom/requirements.txt
      - name: Run pytest
        run: |
          pytest tests/telecom -q
```

Module 6 — Edge, Slicing & Orchestration (3 days)
- Network slicing fundamentals and QoS mapping
- Edge computing & MEC concepts
- Orchestration: VNFs vs CNFs, ETSI MANO basics
- Kubernetes for CNFs: Helm, Operators, service meshes

Hands-on:
- Deploy a sample CNF using Kubernetes (Minikube)
- Use NetworkPolicies and QoS classes to simulate slice constraints

Module 7 — Cloud & Virtualization (2 days)
- OpenStack basics: Nova, Neutron, Cinder, Keystone
- Kubernetes deployment patterns for network functions
- Observability: Prometheus, Grafana, ELK for NF metrics/logs

Hands-on:
- Launch a VM on OpenStack (or simulate with Vagrant)
- Deploy a simple microservice with Helm and monitor with Prometheus

Module 8 — Testing & RCA (2 days)
- Design test cases: unit, integration, system, acceptance
- Structured logging for RCA (JSON logs, correlation IDs)
- Use the repo's RCA engine to parse and identify failures

Hands-on:
- Run telecom tests in `tests/telecom/` and feed logs into `tools/rca_engine/rca_engine.py`

Capstone Project (1–2 weeks)

Build an end-to-end mini lab:
- Deploy Open5GS (4G) or free5GC (5G) in Docker containers
- Deploy Kamailio/OpenSIPS + FreeSWITCH for IMS
- Automate registration and call flow tests via Python/Robot
- Generate logs and run RCA to identify injected faults

Assessment Criteria

- Functional correctness of flows (attach, registration, call)
- Test automation coverage and reliability (CI integration)
- Ability to detect and diagnose faults using logs and RCA
- Documentation and reproducibility of the lab

Suggested Weekly Schedule (Full-time 40h/week)

Week 1: Setup, Mobile Core Fundamentals, IMS basics
Week 2: SIP deep dive, VoLTE, 5G SBA, protocol labs
Week 3: Automation with Python/Robot, CI/CD integration
Week 4: Edge, slicing, orchestration, cloud basics
Week 5: Testing, RCA, capstone implementation and wrap-up

Resources & Reading

- Open5GS: https://open5gs.org/
- free5GC: https://www.free5gc.org/
- Kamailio: https://www.kamailio.org/
- OpenSIPS: https://opensips.org/
- FreeSWITCH: https://freeswitch.org/
- Wireshark: https://www.wireshark.org/
- 3GPP specs: https://www.3gpp.org/
- Robot Framework: https://robotframework.org/
- Scapy: https://scapy.net/
- Kubernetes: https://kubernetes.io/

Sample `telecom/requirements.txt`

```
requests
scapy
pytest
robotframework
aiohttp
python-gelf
```

Notes and Best Practices

- Mask credentials in logs and artifacts; use secure vaults for secrets in CI
- Use structured logs (JSON) and consistent correlation IDs across components
- Start with services in containers before moving to cloud/VM deployments
- Automate incremental tests and integrate them into nightly pipelines

File references

- Learning path saved to: [docs/telecom_network/LEARNING_PATH.md](docs/telecom_network/LEARNING_PATH.md)
- Existing requirements doc: [docs/telecom_network/NETWORK_REQUIREMENTS.md](docs/telecom_network/NETWORK_REQUIREMENTS.md)

