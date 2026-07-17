# Telecom & Network Core Requirements

This document summarizes the "Must Have" and "Good to Have" competencies, architectural considerations, automation recommendations, and suggested validation/test extensions for Telecom & Network features relevant to embedded/networked platforms.

## 1. Telecom & Network Core (Must Have)

- Mobile Core Network
  - EPC / 4G core concepts (MME, HSS, SGW, PGW)
  - 5G Core concepts (AMF, SMF, UPF, NRF)
- IMS Core
  - SIP-based session control
  - Call session management, registration, routing
  - Media proxies and RTP handling
- Network Architecture (Product / Platform Networks)
  - Control plane vs data plane separation
  - Service/management networks, out-of-band management (BMC/Redfish)
  - Edge and core placement considerations
- VoLTE and 5G Core Service Based Architecture (SBA)
  - Network function APIs and service discovery
  - Stateless vs stateful NFs, scaling and HA patterns

## 2. Programming & Automation (Must Have)

- Python
  - Test harness and automation scripts
  - Libraries: requests, asyncio, scapy, pyOpenSSL, asyncssh
- Robot Framework
  - Keyword-driven tests for acceptance-level scenarios
  - Integration with Selenium, SSH, REST libraries
- REST API
  - Test and validate NF REST interfaces (OpenAPI/Swagger)
  - Mocking/simulating API responses
- CI/CD Expertise
  - Pipeline design for build/test/deploy (GitHub Actions, Jenkins, GitLab CI)
  - Containerized test runners, artifact management
  - Automated regression and nightly runs

## 3. Protocol Knowledge (Good to Have)

- SIP (Session Initiation Protocol)
  - SIP methods, headers, dialogs, forking, proxies
  - SIP message traces and troubleshooting call flows
- Diameter
  - AAA and policy control interactions (charging/auth)
- TCP/IP fundamentals
  - Socket programming, routing, NAT traversal, QoS basics
- GTP (GPRS Tunneling Protocol)
  - User-plane tunneling and control-plane interactions in EPC/5GC
- HTTP/HTTP2
  - RESTful API behavior, streaming, gRPC (if applicable)

## 4. Advanced Network Technologies (Good to Have)

- Network Slicing
  - Slice isolation, QoS mapping, orchestration considerations
- Edge Computing
  - MEC concepts, placement of UPF/edge functions
- Orchestration & NFV
  - ETSI MANO basics, VNFs vs CNFs, descriptors, lifecycle
  - Integration with Kubernetes for CNFs

## 5. Cloud & Virtualization (Good to Have)

- Cloud deployment and configuration
  - Infrastructure as Code (Terraform, Ansible)
  - Observability (Prometheus, Grafana, ELK)
- Red Hat OpenStack
  - Basic deployment and networking (Neutron)
  - Nova, Cinder, Keystone basics
- Kubernetes
  - Deploying CNFs as containers
  - Helm charts, Operators, Cluster networking

---

## Suggested Training Modules and Milestones

1. Intro to Mobile Core Networks (2 days)
   - EPC, 5G core basics, high-level call/data flows
2. IMS & SIP Fundamentals (2 days)
   - SIP session flows, basic registrations, INVITE flow troubleshooting
3. Automation with Python & Robot Framework (3 days)
   - Writing API tests, Robot keywords, CI integration
4. Protocol Deep Dive (3 days)
   - GTP, Diameter, advanced TCP/IP, Wireshark trace analysis
5. Cloud & Orchestration (3 days)
   - Kubernetes basics, OpenStack intro, Terraform/Ansible

## Validation & Test Extensions (how to apply to this repo)

- Add `tests/telecom/` suite to the Python test framework
  - `tests/telecom/test_ims_suite.py` — SIP registration, call setup, teardown, failure cases
  - `tests/telecom/test_core_suite.py` — AMF/SMF interactions, session management, GTP tunnels
  - `tests/telecom/test_api_suite.py` — REST API conformance for NFs

- Integration tools and optional emulators
  - Open-source stacks: Open5GS, Magma, Kamailio, FreeSWITCH, Asterisk
  - srsRAN / srsCore for RAN-functional validation (optional)

- Automation & CI
  - Provide `telecom/requirements.txt` for Python dependencies
  - Add Robot Framework pipelines for high-level acceptance tests
  - Use Docker Compose and Kubernetes manifests for integration testbeds

## Tools & Libraries Recommended

- SIP/IMS: Kamailio, OpenSIPS, FreeSWITCH, Asterisk
- 4G/5G Core: Open5GS, free5GC, Magma
- Packet tools: Scapy, tshark, Wireshark
- API testing: Postman, Newman, pytest + requests
- Orchestration: Helm, Terraform, Ansible

## Example Test Case (SIP Registration)

- Test ID: TELECOM_SIP_001
- Precondition: IMS Core reachable, SIP user credential configured
- Steps:
  1. Send SIP REGISTER from UA to IMS proxy
  2. Verify 200 OK and registered state in HSS
  3. Re-register with expired credentials and expect 401
- Expected Result: Registration successful with 200 OK; failed credentials return 401

## Notes

- Keep telecom tests modular: unit-level mocks, integration-level emulators, system-level end-to-end tests.
- Security and privacy: mask credentials in logs and test artifacts.
- Use structured logging (JSON) to feed RCA engine and trace call flows.

