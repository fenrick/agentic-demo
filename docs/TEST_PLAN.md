# Test Plan

This document defines a **comprehensive**, **explicit** Test Plan for the Lecture Builder Agent. It covers all testing activities—unit, integration, end-to-end, performance, security, accessibility, and compliance. Each section specifies objectives, scope, entry/exit criteria, tools, schedules, and responsibilities. No assumptions are made about prior knowledge.

---

## 1. Objectives and Scope

- **Ensure Functional Correctness**: Verify each component meets its specification.
- **Validate Integration**: Confirm seamless interaction across modules and layers.
- **Assess Performance and Scalability**: Test under expected and peak loads.
- **Enforce Security Requirements**: Validate controls defined in SECURITY.md.
- **Verify Accessibility and Compliance**: Ensure UI meets standards and regulatory needs.
- **Maintain Quality Over Time**: Automated tests in CI/CD to catch regressions early.

**Scope**: All backend modules, frontend UX, data flows, APIs, and export pipelines.

---

## 2. Testing Levels

| Level                          | Description                                                      | Tools                                     | Ownership       |
| ------------------------------ | ---------------------------------------------------------------- | ----------------------------------------- | --------------- |
| **Unit Testing**               | Component-level tests for functions, classes, schemas            | Pytest, Jest                              | Devs            |
| **Integration Testing**        | Interaction between backend services, orchestrator workflows, DB | Pytest, Postman, Docker Compose           | Devs            |
| **End-to-End (E2E)**           | Simulate user flows from prompt to download                      | Playwright, Cypress                       | QA              |
| **Performance Testing**        | Throughput, latency, resource utilization under load             | k6, Locust                                | SRE/QoS Team    |
| **Security Testing**           | SAST, DAST, dependency scans, penetration tests                  | Bandit, OWASP ZAP, Trivy, custom pen-test | DevSecOps       |
| **Accessibility Testing**      | WCAG 2.1 AA compliance, keyboard navigation                      | Lighthouse CI, axe-core                   | UX/QA           |
| **Compliance Testing**         | GDPR, Privacy Act, FERPA export/delete flows                     | Manual test scripts, policy checklists    | Compliance Team |
| **Chaos & Resilience Testing** | Fault injection, crash recovery                                  | Gremlin, Chaos Monkey                     | SRE             |

---

## 3. Entry and Exit Criteria

### 3.1 Entry Criteria

- Requirements and designs approved (DESIGN.md, ARCHITECTURE.md, SECURITY.md).
- Test environment provisioned with required services (DB, API keys).
- Test data sets and fixtures available.
- CI/CD pipeline configured with test stages.

### 3.2 Exit Criteria

- All critical and high-severity defects resolved or documented with workarounds.
- Test coverage thresholds met:
  - **Unit**: ≥ 90% lines and branches
  - **Integration**: ≥ 80% of service interactions

- Performance targets achieved (see §5).
- Accessibility audit score ≥ 90% (Lighthouse)
- Security scan results with zero critical vulnerabilities.
- Compliance tests passed with no open findings.

---

## 4. Test Environments and Data

### 4.1 Environments

- **Local**: Developers run unit and integration tests via Docker Compose.
- **CI**: Isolated containers for backend, frontend, DB (SQLite or ephemeral Postgres).
- **Staging**: Mirroring production topology in Kubernetes namespace `staging`.
- **Production**: Smoke tests only; no destructive tests.

### 4.2 Test Data

- **Prompt Samples**: Variety of topics, lengths, edge cases (empty, special characters).
- **Citation Fixtures**: Mock Perplexity Sonar responses with valid/invalid licenses.
- **State Snapshots**: Pre-generated snapshots for resume tests.
- **User Roles**: Token sets for `viewer`, `editor`, `admin` to test RBAC.

All test data stored in `tests/fixtures/` with version control.

---

## 5. Performance and Scalability

### 5.1 Performance Objectives

- **Prompt-to-first-stream latency**: P95 < 2 seconds under 50 concurrent users.
- **End-to-End completion time**: P95 < 30 seconds for a 5-module outline.
- **Export generation time**: Markdown < 1s, DOCX < 3s, PDF < 5s.
- **SSE throughput**: ≥ 100 events/sec sustained.

### 5.2 Tools and Scripts

- **k6**: Scenario scripts in `performance/k6/` to simulate user flows.
- **Locust**: Python-based locustfile in `performance/locust/` for mixed workload tests.
- **CI Integration**: Run performance tests in nightly pipeline; fail build on regressions >10%.

### 5.3 Monitoring and Reporting

- Capture metrics via Prometheus; compare against baselines in Grafana.
- Performance reports stored as artifacts in CI runs.

---

## 6. Security Testing

### 6.1 Static Application Security Testing (SAST)

- **Tools**: Bandit for Python, ESLint security plugins for JS.
- **Coverage**: All code scanned on each PR; block merge on high/critical findings.

### 6.2 Dynamic Application Security Testing (DAST)

- **Tools**: OWASP ZAP against staging environment.
- **Tests**: SQLi, XSS, authentication bypass, API fuzzing.
- **Schedule**: Weekly automated scans; quarterly manual black-box tests.

### 6.3 Dependency Scanning

- **Tools**: pip-audit, npm audit, Trivy for container images.
- **Policy**: Zero unpatched critical CVEs; medium must have documented risk acceptance.

### 6.4 Penetration Testing

- **Scope**: External infrastructure (API endpoints, UI) and internal components.
- **Frequency**: Bi-annual by third-party firm.
- **Deliverables**: Report with severity ratings, remediation plan.

---

## 7. Accessibility Testing

### 7.1 Standards

- **WCAG 2.1 AA** compliance mandatory.

### 7.2 Test Tools

- **Lighthouse CI**: automated checks in CI for color contrast, ARIA roles.
- **axe-core**: programmatic audits for dynamic content.
- **Manual Testing**: Keyboard-only navigation tests, screen reader flow (NVDA/VoiceOver).

### 7.3 Reporting

- Accessibility reports archived in CI artifacts; remediation tracked in backlog.

---

## 8. Compliance Testing

### 8.1 Data Privacy

- **GDPR Flow Tests**: Verify data export (`/user/export`) and deletion (`/user/delete`) per user.
- **Australian Privacy Act**: Confirm local data residency and PII handling.

### 8.2 FERPA (Optional)

- **Tests**: Role-based access to student content; audit log verification.

### 8.3 Audit Readiness

- **Checklists**: Execute `docs/COMPLIANCE/AUDIT_CHECKLIST.md` pre-release.

---

## 9. End-to-End and Integration Testing

### 9.1 E2E Test Scenarios

1. **Happy Path**: User submits topic, watches streaming, downloads all formats.
2. **Retry Path**: Interrupt job mid-stream, retry, and complete.
3. **Error Path**: Researcher API failure triggers retry logic, then fallback to cache.
4. **RBAC Enforcement**: `viewer` cannot start jobs; `editor` can.
5. **Invalid Input**: Empty or malicious prompt yields validation error.

### 9.2 Integration Points

- **Orchestrator nodes**: unit test each node and mock downstream calls.
- **DB Integration**: Use ephemeral Postgres for SQL queries, checkpoint writes and reads.
- **External APIs**: Mock ChatPerplexity and OpenAI via local stub server in tests.

---

## 10. Chaos and Resilience Testing

- **Gremlin Experiments**: Inject latency, pod restarts, disk failures in staging.
- **Recovery Validation**: Ensure resumes within 500ms and no data loss.
- **Reporting**: Document incidents and recovery timelines.

---

## 11. Test Automation and CI/CD Integration

- **Pipeline Stages**:
  1. **Install & Lint**: `flake8`, `eslint`
  2. **Unit/Integration**: `pytest`, `jest`
  3. **E2E**: `playwright` or `cypress` against staging deploy preview
  4. **Security**: SAST, dependency scans, DAST
  5. **Performance**: k6 baseline run (nightly)
  6. **Accessibility**: Lighthouse CI
  7. **Compliance**: Checklist script

- **Failure Policies**: Block merges on test failures; nightly alerts on performance regressions.

---

## 12. Reporting and Metrics

- **Test Coverage**: Codecov reports for Python/JS; target thresholds enforced.
- **Defect Tracking**: Jira project `LECTURE_AGNT`, severity mapping.
- **Metrics Dashboard**: Grafana panels for pass rates, test duration, defect densities.
- **Release Readiness**: QA sign-off checklist in pull request template.

---

## 13. Roles and Responsibilities

| Role                | Responsibilities                                      |
| ------------------- | ----------------------------------------------------- |
| **Developers**      | Write unit and integration tests; fix defects         |
| **QA Engineers**    | Author E2E, performance, and accessibility tests      |
| **DevSecOps**       | Implement security scans; review SAST/DAST results    |
| **SRE/QoS Team**    | Performance test script maintenance; chaos tests      |
| **Compliance Team** | Compliance test execution and reporting               |
| **Product Owner**   | Define acceptance criteria; approve test plan updates |

---

## 14. Next Steps

1. **Review & Baseline**: QA team to approve this Test Plan.
2. **Implement Scripts**: Develop k6, Playwright, and Cypress scripts.
3. **CI Setup**: Integrate tests into pipeline and configure alerting.
4. **Dry Run**: Execute full test suite against staging; document findings.
5. **Iterate**: Refine tests and thresholds based on initial results.

_End of Test Plan for Lecture Builder Agent._
