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

- **Purpose**: Verifies database connectivity and research client availability.
- **Authentication**: None
- **Response**:
  - **200 OK**: `{ "status": "ok" }`
  - **500 Internal Server Error**: `{ "status": "error", "details": "<error message>" }`

### 2.2 GET `/metrics`

- **Purpose**: Exposes Prometheus-formatted metrics.
- **Authentication**: None (secured by network policy).
- **Response**: Plaintext Prometheus metrics including counters for HTTP requests,
  active SSE clients, and export durations. Example:

  ```plaintext
  # HELP requests_total HTTP requests received
  requests_total 5
  # HELP sse_clients Active SSE client connections
  sse_clients 1
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

The `POST /api/resume/{job_id}` endpoint is **not yet implemented** and currently
returns `501 Not Implemented` for all requests.

---

## 4. Server-Sent Events (SSE)

Clients subscribe to four SSE endpoints to receive real-time updates. Each
stream sends newline-delimited JSON messages where the `event` field indicates
the channel and the payload conforms to the `SseEvent` schema (`type`,
`payload`, `timestamp`).

### 4.1 Token Messages

#### GET `/api/stream/messages`

- **Purpose**: Stream token-level diff messages from LLMs.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: messages` followed by a serialized `SseEvent`.

### 4.2 Updates

#### GET `/api/stream/updates`

- **Purpose**: Stream citation additions and workflow progress updates.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: updates` with an `SseEvent` payload.

### 4.3 Values

#### GET `/api/stream/values`

- **Purpose**: Stream structured state values as they change.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: values` followed by an `SseEvent`.

### 4.4 Debug

#### GET `/api/stream/debug`

- **Purpose**: Stream diagnostic or debug messages.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: debug` followed by an `SseEvent`.

### 4.5 Workspace-Scoped Streams

Every channel above also supports a workspace-scoped variant that isolates
events to a single workspace.

#### GET `/api/stream/{workspace_id}/messages`

- **Purpose**: Stream token-level diff messages for a specific workspace.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: messages` with an `SseEvent` payload.

#### GET `/api/stream/{workspace_id}/updates`

- **Purpose**: Stream citation additions and workflow progress updates for a
  workspace.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: updates` with an `SseEvent` payload.

#### GET `/api/stream/{workspace_id}/values`

- **Purpose**: Stream structured state values for a workspace.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: values` followed by an `SseEvent`.

#### GET `/api/stream/{workspace_id}/debug`

- **Purpose**: Stream diagnostic messages for a workspace.
- **Authentication**: Required (`viewer`, `editor`, or `admin`).
- **Event Format**: `event: debug` followed by an `SseEvent`.

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
