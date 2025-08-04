# API Reference

This document provides a **detailed**, **explicit** reference for all backend HTTP and SSE endpoints of the Lecture Builder Agent. No assumptions are made about prior knowledge; every parameter and response is defined.

---

## 1. Authentication and Base Path

- **Base URL**: `https://<your-domain>/api`
- **Authentication**: All endpoints (except `/healthz` and `/metrics`) require a valid JSON Web Token (JWT).
  - Send in HTTP header:

    ```http
    Authorization: Bearer <JWT_TOKEN>
    ```

---

## 2. Health and Metrics

### 2.1 GET `/healthz`

- **Purpose**: Liveness and readiness check.
- **Authentication**: None
- **Response**:
  - **200 OK**: `{ "status": "ok" }`
  - **500 Internal Server Error**: `{ "status": "error", "details": "<error message>" }`

### 2.2 GET `/metrics`

- **Purpose**: Exposes Prometheus-formatted metrics.
- **Authentication**: None (secured by network policy).
- **Response**: Plaintext Prometheus metrics. Example:

  ```plaintext
  # HELP http_request_duration_seconds ...
  http_request_duration_seconds_bucket{le="0.5"} 42
  ...
  ```

---

## 3. Job Management

### 3.1 Start New Lecture Build

#### POST `/api/run`

- **Purpose**: Begin a new lecture/workshop generation job.

- **Authentication**: Required (`editor` or `admin`).

- **Request Body (JSON)**:

  | Field     | Type   | Required | Description                               |
  | --------- | ------ | -------- | ----------------------------------------- |
  | `topic`   | String | Yes      | Lecture or workshop prompt string.        |
  | `options` | Object | No       | Optional settings (e.g. model overrides). |

- **Response (JSON)**:
  - **201 Created**

    ```json
    { "job_id": "123e4567-e89b-12d3-a456-426614174000" }
    ```

  - **400 Bad Request**: Invalid or missing `topic`.
  - **401 Unauthorized**: Missing or invalid JWT.

### 3.2 Resume Existing Job

#### POST `/api/resume/{job_id}`

- **Purpose**: Resume a previously interrupted job.

- **Authentication**: Required (`editor` or `admin`).

- **Path Parameter**:

  | Parameter | Type   | Description                |
  | --------- | ------ | -------------------------- |
  | `job_id`  | String | UUID of the job to resume. |

- **Response (JSON)**:
  - **200 OK**

    ```json
    { "job_id": "<same-id>", "status": "resumed" }
    ```

  - **404 Not Found**: No job with given `job_id`.
  - **401 Unauthorized**: Invalid JWT.

---

## 4. Server-Sent Events (SSE)

Clients subscribe to three SSE endpoints to receive real-time updates. Each SSE stream sends newline-delimited JSON messages.

### 4.1 State Snapshots

#### GET `/api/stream/state?job_id=<job_id>`

- **Purpose**: Stream structured state snapshots as each agent completes.

- **Authentication**: Required (`viewer`, `editor`, or `admin`).

- **Query Parameter**:

  | Parameter | Type   | Required | Description      |
  | --------- | ------ | -------- | ---------------- |
  | `job_id`  | String | Yes      | UUID of the job. |

- **Event Format**: `event: state` followed by JSON data.

  ```plaintext
  event: state
  data: { "version": 1, "learning_objectives": ["..."], "modules": [...] }
  ```

### 4.2 Action Log

#### GET `/api/stream/actions?job_id=<job_id>`

- **Purpose**: Stream chronological action records from agents.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: action`.

  ```plaintext
  event: action
  data: { "timestamp": "2025-08-04T10:15:30Z", "agent": "Researcher-Web", "message": "Fetched 5 citations", "tokens": 123, "cost_usd": 0.01 }
  ```

### 4.3 New Citations

#### GET `/api/stream/citations?job_id=<job_id>`

- **Purpose**: Stream citation objects as they are added.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: citation`.

  ```plaintext
  event: citation
  data: { "citation_id": "c1", "url": "https://example.edu/paper", "title": "...", "retrieved_at": "...", "license": "CC-BY" }
  ```

---

## 5. Downloads

### 5.1 Retrieve Final Artefact

#### GET `/api/download/{job_id}/{format}`

- **Purpose**: Download the completed lecture package.

- **Authentication**: Required (`viewer`, `editor`, or `admin`).

- **Path Parameters**:

  | Parameter | Type   | Description                      |
  | --------- | ------ | -------------------------------- |
  | `job_id`  | String | UUID of the completed job.       |
  | `format`  | String | One of `markdown`, `docx`, `pdf` |

- **Response**:
  - **200 OK**: Binary stream with appropriate `Content-Type`.

    | Format     | Content-Type                                                              |
    | ---------- | ------------------------------------------------------------------------- |
    | `markdown` | `text/markdown; charset=utf-8`                                            |
    | `docx`     | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
    | `pdf`      | `application/pdf`                                                         |

  - **404 Not Found**: Job incomplete or wrong `job_id`.

  - **400 Bad Request**: Unsupported format.

---

## 6. Error Responses

All error responses (except SSE) use JSON:

```json
{
  "error": {
    "code": "<ERROR_CODE>",
    "message": "<detailed human-readable message>",
    "details": <optional object>
  }
}
```

| HTTP Status | Common Error Codes      | Description                                  |
| ----------- | ----------------------- | -------------------------------------------- |
| 400         | `INVALID_INPUT`         | Malformed request or missing required field. |
| 401         | `UNAUTHORIZED`          | Missing or invalid authentication token.     |
| 403         | `FORBIDDEN`             | Authenticated but lacking permissions.       |
| 404         | `NOT_FOUND`             | Resource (job, format) not found.            |
| 500         | `INTERNAL_SERVER_ERROR` | Unhandled exception on server.               |

---

## 7. Rate Limiting and Quotas

- **Per-IP Rate Limit**: 100 requests per minute for job management endpoints.
- **Per-User Quota**: 10 concurrent jobs per user; additional requests return **429 Too Many Requests**:

  ```json
  {
    "error": {
      "code": "RATE_LIMIT_EXCEEDED",
      "message": "Too many concurrent jobs."
    }
  }
  ```

---

## 8. Versioning and Deprecation

- **API Version**: v1 (embedded in Base URL as `/api/v1` in future releases).
- **Deprecation Policy**: Deprecated endpoints will return `410 Gone` with a link to migration guide.

---

_End of API Reference._
