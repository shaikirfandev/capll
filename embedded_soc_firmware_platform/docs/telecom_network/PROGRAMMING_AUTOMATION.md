# Programming & Automation — Learning Guide

This guide expands the "Programming & Automation (Must Have)" competencies from the job description into an actionable learning module focused on Python, Robot Framework, REST API testing, and CI/CD automation.

Audience: Test engineers, automation engineers, and firmware validation engineers.

Duration: 1–2 weeks (intensive) or 4–6 weeks (part-time).

Prerequisites

- Familiarity with Python (basic scripting)
- Linux command-line experience
- Git and basic CI concepts

Learning Objectives

- Build robust automation scripts in Python for network/firmware validation
- Develop keyword-driven Robot Framework tests for acceptance-level scenarios
- Design and run REST API tests and contract checks for NFs
- Integrate automation into CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)

Module 1 — Python for Telecom Automation (2 days)

Topics:
- Python basics: virtual environments, packaging, modules
- Networking libraries: `requests`, `aiohttp`, `paramiko` for SSH
- Packet manipulation: `scapy` for SIP/GTP crafting
- Async programming for high-throughput tests (`asyncio`)
- Test frameworks: `pytest` for unit and integration tests

Hands-on:
- Create a Python virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install requests aiohttp scapy pytest
```

- Implement a small script to perform a REST GET against a mock NF

```python
import requests

resp = requests.get('http://localhost:8080/api/status')
print(resp.status_code, resp.json())
```

Module 2 — Robot Framework (2 days)

Topics:
- Keyword-driven testing model
- Test libraries: `RequestsLibrary`, `SSHLibrary`, `SeleniumLibrary` (if needed)
- Writing reusable keywords and resource files
- Reporting and logs

Hands-on:
- Install Robot Framework and RequestsLibrary

```bash
pip install robotframework robotframework-requests
```

- Example Robot test: `tests/robot/telecom_acceptance.robot`

```
*** Settings ***
Library    RequestsLibrary

*** Variables ***
${BASE}    http://localhost:8080

*** Test Cases ***
SIP Registration Should Succeed
    Create Session    telecom    ${BASE}
    ${resp}=    Get Request    telecom    /register?user=test
    Should Be Equal As Integers    ${resp.status_code}    200
```

Module 3 — REST API Testing & Contract Validation (1 day)

Topics:
- OpenAPI/Swagger-based contract tests
- Schema validation using `jsonschema` or `schemathesis`
- Mocking and stubbing NF APIs for unit tests

Hands-on:
- Validate a sample OpenAPI spec with `schemathesis`

```bash
pip install schemathesis
schemathesis run http://localhost:8080/openapi.json
```

Module 4 — CI/CD Integration (2 days)

Topics:
- Design pipelines for build/test/deploy
- Containerized test runners using Docker
- Scheduling nightly/regression runs
- Storing artifacts and test reports

Hands-on: GitHub Actions example to run pytest

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

Module 5 — Best Practices & Patterns (1 day)

- Use virtualenvs for isolation
- Keep credentials out of code — use secrets managers
- Use structured logging (JSON) with correlation IDs
- Use retries and backoff for flaky network operations
- Build idempotent tests
- Add cleanup steps in teardown to avoid resource leaks

Deliverables

- `telecom/requirements.txt` — list of pip packages for telecom testing
- Robot Framework acceptance tests (example)
- CI pipeline snippet (GitHub Actions) for running tests

Sample `telecom/requirements.txt`

```
requests
scapy
pytest
robotframework
robotframework-requests
aiohttp
python-gelf
pyOpenSSL
paramiko
```

Next Steps

- Create example Robot Framework tests under `tests/robot/`
- Wire Robot tests into CI pipeline
- Add sample scripts for REST contract testing with `schemathesis`

File location: `docs/telecom_network/PROGRAMMING_AUTOMATION.md`
