# CI/CD Setup Guide
## TCU Validation Framework v2.0.0

---

## 1. GitHub Actions

The workflow file is at `.github/workflows/ci.yml`.

### 1.1 Trigger conditions
- Push to `main`, `develop`, `release/**`
- Pull request targeting `main` or `develop`

### 1.2 Jobs

| Job | Runs on | Description |
|-----|---------|-------------|
| `build-and-test` | ubuntu-22.04 | Build + unit + integration tests |
| `static-analysis` | ubuntu-22.04 | cppcheck + clang-tidy |
| `coverage` | ubuntu-22.04 | gcovr HTML + XML coverage |
| `docker` | ubuntu-22.04 | Docker image build (cache-optimised) |
| `package` | ubuntu-22.04 | CPack DEB + TGZ (tags only) |

### 1.3 Repository secrets (optional)
For pushing Docker images to a registry:

| Secret | Description |
|--------|-------------|
| `DOCKER_USERNAME` | Registry username |
| `DOCKER_PASSWORD` | Registry password / PAT |
| `SONAR_TOKEN` | SonarQube project token |

Add secrets in GitHub: **Settings → Secrets and variables → Actions**.

### 1.4 Branch protection (recommended)
Under **Settings → Branches → Branch protection rules** for `main`:
- [x] Require status checks: `build-and-test (ubuntu-22.04, Debug)`, `static-analysis`
- [x] Require branches to be up to date
- [x] Require pull request reviews (1 approver)

---

## 2. Jenkins Pipeline

The `Jenkinsfile` uses the declarative pipeline syntax with Docker agent.

### 2.1 Requirements

**Jenkins plugins:**
- Pipeline
- Docker Pipeline
- JUnit (for test result publishing)
- HTML Publisher (for coverage reports)
- Warnings Next Generation (for cppcheck/clang-tidy)

Install via Manage Jenkins → Plugin Manager.

### 2.2 Create a pipeline job
1. New Item → Pipeline
2. Under **Pipeline → Definition**: select **Pipeline script from SCM**
3. SCM: Git, repository URL, branch `*/main`
4. Script path: `Jenkinsfile`
5. Save → Build Now

### 2.3 Agent requirements
The Jenkinsfile uses a Docker agent (`ubuntu:22.04`) with `--privileged` for `modprobe vcan`.  
Your Jenkins agent must:
- Have Docker installed and the Jenkins user in the `docker` group
- Have `--privileged` allowed (edit Jenkins Docker plugin settings)

### 2.4 Environment variables in Jenkins
Add under **Manage Jenkins → System → Global properties → Environment variables**:

| Variable | Value |
|----------|-------|
| `BUILD_TYPE` | `Debug` |
| `DEBIAN_FRONTEND` | `noninteractive` |

---

## 3. SonarQube Integration

### 3.1 Prerequisites
- SonarQube server (Community Edition is free)
- `sonar-scanner` CLI installed on the build agent
- Build Wrapper for C/C++ (`build-wrapper-linux-x86-64`)

### 3.2 Install build wrapper
```bash
# Download from your SonarQube server
wget http://your-sonar-server/static/cpp/build-wrapper-linux-x86-64.zip
unzip build-wrapper-linux-x86-64.zip
sudo cp build-wrapper-linux-x86-64/build-wrapper-linux-x86-64 /usr/local/bin/
```

### 3.3 Run analysis
```bash
# Wrap the build with build-wrapper
build-wrapper-linux-x86-64 --out-dir bw-output \
    cmake --build build/Debug --parallel $(nproc)

# Run sonar-scanner
sonar-scanner \
    -Dsonar.host.url=http://your-sonar-server \
    -Dsonar.login=$SONAR_TOKEN
```

### 3.4 sonar-project.properties
The file at the project root is pre-configured. Update these fields for your server:
```properties
sonar.projectKey=tcu_validation_framework
sonar.host.url=http://your-sonar-server:9000
```

---

## 4. Docker Registry Publishing

### 4.1 GitHub Container Registry (ghcr.io)
Add to `.github/workflows/ci.yml` after the docker build step:
```yaml
- name: Login to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: ${{ github.ref == 'refs/heads/main' }}
    tags: ghcr.io/${{ github.repository_owner }}/tcu-validation-framework:latest
```

---

## 5. Artifact Management

### GitHub Actions artifacts
Test XML reports and coverage HTML are uploaded as artifacts per run.  
Download from the Actions run page: **Artifacts → test-results-Debug-ubuntu-22.04**.

Artifacts expire after 90 days by default. Adjust in the workflow:
```yaml
- uses: actions/upload-artifact@v4
  with:
    retention-days: 30
```

### Jenkins build archiving
Artifacts are archived via `archiveArtifacts` in the Jenkinsfile.  
Access from the build page: **Build Artifacts**.

---

## 6. Quality Gates

### 6.1 Current checks
- All unit tests pass (GoogleTest)
- All integration tests pass
- cppcheck finds no errors (warnings allowed)
- clang-tidy produces no errors

### 6.2 Recommended additions
- Minimum 80% line coverage (enforce via gcovr `--fail-under-line 80`)
- SonarQube quality gate (A-rated maintainability)
- No new critical/blocker issues in PRs

### 6.3 Enforce coverage in CI
```yaml
- name: Enforce coverage threshold
  run: |
    gcovr \
      --root src/ \
      --fail-under-line 80 \
      --xml reports/coverage.xml \
      --exclude tests/ --exclude build/
```
