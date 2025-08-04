# Security Documentation

## 1. Purpose and Scope

This document provides a **comprehensive**, **explicit** security specification for the Lecture Builder Agent. It covers threat modeling, controls, and compliance measures. No assumptions are made about environment or prior knowledge.

**Includes:**

- Threat and risk assessment
- Authentication, authorization, and identity management
- Secrets management and credential rotation
- Data protection (encryption, retention, sanitization)
- Network, infrastructure, and runtime security
- Dependency and supply chain security
- Logging, monitoring, and incident response
- Compliance with relevant regulations

---

## 2. Threat Model and Risk Assessment

### 2.1 Assets

- **User Data:** Prompts, generated lecture content, citations
- **Service Secrets:** API keys (OpenAI, Perplexity Sonar), vault tokens
- **Persistent Data:** SQLite/Postgres databases, cache, logs, document versions
- **Infrastructure:** Compute resources, container images, network endpoints

### 2.2 Threat Actors

- **External Attackers:** Attempt unauthorized API access, data exfiltration
- **Insiders:** Malicious or careless developers/operators
- **Supply Chain Actors:** Dependency compromise, container registry compromise

### 2.3 Threat Scenarios

| ID  | Scenario                                                                     | Impact                       | Likelihood | Mitigation Reference |
| --- | ---------------------------------------------------------------------------- | ---------------------------- | ---------- | -------------------- |
| T1  | Compromised OpenAI API key used to generate malicious content or incur costs | Data integrity, cost overrun | Medium     | §3, §4               |
| T2  | Unauthorized user accesses draft content or logs                             | Confidentiality breach       | Medium     | §5                   |
| T3  | Theft of database file from local disk or backup                             | Data breach (user data, IP)  | Low        | §6.2, §6.3           |
| T4  | Dependency vulnerability leads to remote code execution                      | Full system compromise       | Medium     | §8                   |
| T5  | SSE connection hijack to view streaming tokens                               | Information leakage          | Low        | §5.4                 |

Risk assessment assumes default deployment in a secure network.

---

## 3. Authentication & Authorization

### 3.1 API Authentication

- **Mechanism:** JSON Web Tokens (JWT) signed with RS256
- **Issuance:** Users authenticate via SSO (OIDC) or local credentials; Auth service issues JWT with 1h expiry
- **Validation:** FastAPI middleware validates signature and checks `exp` claim

### 3.2 Role-Based Access Control (RBAC)

- **Roles:** `viewer`, `editor`, `admin`
- **Permissions matrix:** documented in `backend/auth/permissions.yaml`
  - `viewer`: read-only access to running jobs and downloads
  - `editor`: run/resume jobs, view logs and citations
  - `admin`: full access including security endpoints, key rotation

- **Enforcement:** FastAPI dependencies guard each endpoint

### 3.3 SSE & Websocket Security

- **Authentication:** JWT passed as query param or Authorization header
- **Connection:** TLS only
- **Authorization:** Token validated before stream established; streams scoped to `job_id` role

---

## 4. Secrets Management

### 4.1 Storage and Access

- **HashiCorp Vault** as primary secrets store
  - Mounted via Kubernetes CSI driver or Vault Agent injector
  - Secrets (OpenAI_API_KEY, PERPLEXITY_API_KEY, GPG_SIGN_KEY) injected at container runtime

- **Local Development:** `dotenv` files only; CI pipeline rejects commits with `.env` containing real credentials

### 4.2 Rotation and Revocation

- **Rotation policy:** Rotate each API key every 90 days
- **Automation:** Vault dynamic secrets TTL set to 30 days; CI/CD triggers rotation and propagates to deployments
- **Revocation:** On compromise, revoke in Vault UI and trigger redeployments

### 4.3 Encryption of Secrets at Rest

- Vault uses AES-256-GCM to encrypt secrets
- Backups of Vault storage encrypted via customer-managed KMS

---

## 5. Data Protection

### 5.1 Encryption In Transit

- **TLS 1.2+** enforced for all HTTP, SSE, and DB connections
- **Certificates:** Managed via Let’s Encrypt or enterprise CA, auto-renewed

### 5.2 Encryption At Rest

- **SQLite:** SQLCipher with AES-256; key provided via Vault at startup
- **Postgres:** Data encrypted via Transparent Data Encryption (TDE) or disk encryption
- **Backups:** Encrypted before storage in S3 or NFS, using KMS

### 5.3 Data Retention & Purging

- **State Snapshots:** Retain last 50 per `job_id`; older snapshots purged daily via cron job
- **Logs & Metrics:** Retain 30 days; then auto-archive to cold storage (encrypted)
- **Cache:** Citation cache TTL = 7 days; eviction via LRU

### 5.4 Data Sanitization & Least Privilege

- **Input Validation:** Prompt content sanitized for XSS before echoing in UI
- **DB Access:** Service account limited to required schemas; no superuser privileges

---

## 6. Infrastructure & Deployment Security

### 6.1 Container Hardening

- **Base Images:** `python:3.11-slim` and `node:18-alpine` scanned daily
- **Image Scanning:** CI pipeline runs `Trivy` to detect vulnerabilities; fails on high/critical
- **Non-root Execution:** Containers run under `appuser` with UID/GID mapping
- **Minimal Privileges:** Drop all Linux capabilities except `CAP_NET_BIND_SERVICE`

### 6.2 Host & Network

- **Kubernetes Namespaces:** Separate `dev`, `staging`, `prod`
- **Network Policies:** `NetworkPolicy` restricts pod-to-pod and ingress:
  - Only FastAPI pods accept inbound on port 8000
  - Database pods only accept from FastAPI namespace

- **Ingress:** NGINX with WAF rules to block SQLi, XSS

### 6.3 CI/CD Pipeline Security

- **Platform:** GitHub Actions or GitLab CI in isolated runner
- **Checks:** SAST (Bandit for Python), dependency audit (`npm audit`, `pip-audit`), container scan (Trivy)
- **Secrets in CI:** Stored in encrypted secrets store; never printed in logs
- **Branch Protection:** Require code review, status checks, signed commits optional

---

## 7. Dependency & Supply Chain Security

### 7.1 Python Dependencies

- **Pinning:** All `requirements.txt`/`pyproject.toml` dependencies pinned to SHA or version ranges
- **Audit:** `pip-audit` nightly job; dependencies must have zero unpatched CVEs

### 7.2 Node.js Dependencies

- **Lockfile:** `package-lock.json` committed
- **Audit:** `npm audit --audit-level=moderate` in CI

### 7.3 Container Registry

- **Private Registry:** Images pushed to private ECR/GCR
- **Image Signing:** Optional Notary signatures

### 7.4 Third-Party Code Review

- **Manual review** for any package with MIT/BSD license; avoid GPL-licensed dependencies
- **License scanning** via `license-checker`

---

## 8. Logging, Monitoring & Alerting

### 8.1 Logging

- **Structured JSON logs** via `loguru` with fields: `timestamp, level, module, message, job_id, user_id`
- **Central configuration** in `core/logging.py` binds `job_id` and `user_id` across the application.
- **Log Aggregation:** ELK stack (Elasticsearch, Logstash, Kibana) or hosted Splunk
- **Retention:** 30 days, then archived

### 8.2 Metrics & Monitoring

- **Prometheus Metrics:** HTTP request latency, SSE events count, model-call duration, cache hit rate, unsupported-claim rate
- **Dashboards:** Grafana dashboards for each metric category
- **Alerts:** PagerDuty integration for high error rates, latency P95 > 3s, unsupported-claim rate > 2%

### 8.3 Incident Response

- **Playbooks:** Stored in `docs/INCIDENT_RESPONSE.md`
- **Contacts:** On-call rotation via OpsGenie
- **Postmortem:** All incidents >1 hour require formal postmortem within 72 hours

### 8.4 Tracing

- **OpenTelemetry** initialized in `src/web/main.py` with console exporter.
- **Span propagation** ensures all agent nodes participate in request traces.

---

## 9. Compliance & Regulatory

- **Australian Privacy Act:** Handles student-related PII in compliance
- **GDPR:** Users can request data export/deletion; data retention policies support erasure
- **FERPA (US):** No direct student data stored unless configured; document accordingly
- **ISO 27001:** Controls mapped to Annex A; evidence stored in `docs/COMPLIANCE/`

---

## 10. Security Testing & Validation

| Test Type           | Tool/Method          | Frequency   | Owner          |
| ------------------- | -------------------- | ----------- | -------------- |
| SAST                | Bandit               | On each PR  | DevSecOps Team |
| Dependency Audit    | pip-audit, npm audit | Nightly     | CI Pipeline    |
| Container Scan      | Trivy                | On build    | CI Pipeline    |
| Penetration Testing | Manual / 3rd party   | Quarterly   | Security Team  |
| Fuzz Testing        | Hypothesis           | Bi-monthly  | QA Team        |
| Chaos Testing       | Gremlin              | Bi-annually | SRE Team       |

---

## 11. Next Steps and Governance

1. **Review & Approval:** Security team to review this document and sign off.
2. **Integration:** Implement controls in CI/CD and deployment manifests.
3. **Auditing:** Schedule internal audit to validate encryption, RBAC, and secrets management.
4. **Training:** Developer onboarding with security checklist from this doc.

---

_End of Security Documentation for Lecture Builder Agent._
