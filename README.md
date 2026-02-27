# Offboarding

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-009688.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ed.svg)

Internal system for automating and standardizing the employee offboarding process, with integration to Active Directory, InTouch system, Gmail, and ControlID.

---

## 1. Objective

The goal of Offboarding is to automate the process of terminating or suspending employees in the corporate environment, reducing:

- Manual operational errors
- Inconsistencies in account deactivation
- Lack of traceability
- Process execution time

The system acts directly on Active Directory via LDAP and maintains a locally persisted audit trail.

---

## 2. Architecture

The application follows a layered architecture model with separation of responsibilities:

- **API Layer (FastAPI)** → exposure of REST endpoints
- **Service Layer** → business rules
- **Integration Layer (LDAP)** → communication with Active Directory
- **Persistence Layer (SQLite)** → storage of audit logs
- **Frontend Layer** → lightweight administrative interface

### Simplified Diagram

```markdown
Client (Browser)
    ↓
REST API (FastAPI)
    ↓
Service Layer
    ↓
├── LDAP Integration (ldap3)
├── InTouch Integration
├── Gmail Integration
├── ControlID integration
└── SQLite (Audit) Logs
```

---

## 3. Technology Stack

### 3.1 Backend — FastAPI

- Modern ASGI Framework
- Strong typing via Pydantic
- Automatic data validation
- Automatic documentation (OpenAPI/Swagger)
- High performance based on Starlette + Uvicorn

Choosing FastAPI allows for rapid development while maintaining architectural clarity and rigorous data input validation.

---

### 3.2 Database — SQLite

- Embedded relational database
- Zero dependence on external infrastructure
- Ideal for lightweight persistence
- Easy backup and portability

SQLite fully meets the internal audit requirement without the need for a dedicated server.

---

### 3.3 Integration with Active Directory

- Library: `ldap3`

- Operations performed:

- User search

- `userAccountControl` change

- Attribute update (e.g., description)

- Movement to a specific OU

The library allows a direct and secure connection to the Active Directory system.

--

### 3.4 Integration with InTouch

- Connection with `requests`
- Operations performed:

- User search

- User deactivation by registration number

### 3.5 Frontend

- HTML + TailwindCSS
- Communication via Axios (HTTP client)
- Interface focused on internal administrative use
- No dependency on complex SPA frameworks

The choice prioritizes simplicity, speed of implementation, and reduced maintenance.

---

### 3.6 Containerization — Docker

The system runs via Docker container for:

- Dependency isolation
- Standardization of the execution environment
- Ease of deployment on a local network
- Compatibility with already containerized infrastructure

---

## 4. Technical Features

### 4.1 User Search

- Search via registration number or identifier
- Query in Intouch
- Structured return via typed schema

---

### 4.2 User Deactivation

Process executed:

#### 4.2.1 Active Directory

1. Locates user in AD
2. Updates `userAccountControl`
3. Updates `description` field with action history
4. Moves the object to the deactivated OU
5. Logs operation audit

#### 4.2.2 Intouch

1. Locates user in Intouch
2. Updates status by endpoint
3. Logs audit Operation

---

### 4.3 Auditing

Each operation generates a log containing:

- Action
- Status
- Message
- Executing User
- Affected User
- Affected Resource
- IP Address
- User Agent
- Timestamp

Supported export formats:

- CSV
- JSONL
- PDF
- XLSX

---

## 5. Project Structure

```markdown
app/
├── audit/ # Logs and export
├── config/ # Config files
├── database/ # Database configuration
├── services/ # Business rules
├── routers/ # API endpoints
├── schemas/ # Pydantic models
├── security/ # Security settings
├── enums/ # Utilities
├── models/ # Classes and definition of Tables
├── assets # CSS and JavaScript files for the interface
└── main.py # Application initialization
```

---

## 6. Security

- Dedicated service credentials for LDAP
- Persistent logs for traceability
- Isolated container
- Future possibilities:
  - Integration with AD for authentication
  - Permission control by profile

---

## 7. Execution

### 7.1 Prerequisites

- Docker and Docker Compose installed
- Secrets configured in Portainer or local environment

### 7.2 Deployment via Docker Compose

```bash
# Build and start the system
docker-compose up -d --build

```

#### The application will be available at

`http://localhost:8000`

---

## 8. Scalability Considerations

The architecture already allows decoupling of the persistence layer.

The use of Docker facilitates migration to orchestrated environment.

## 9. Configuration & Environment Variables

The system uses a hybrid configuration model: Environment Variables for general settings and *Docker Secrets* for sensitive data.

### 9.1 Environment Variables (Non-sensitive)

These can be defined directly in the docker-compose.yml or via the Portainer environment UI.

| Variable | Description | Example |
| :--- | :---: | ---: |
| ALGORITHM | Encryption algorithm for JWT | HS256 |
| EMAIL_SENDER | Email address that sends notifications | <alerts@cladtek.com> |
| EMAIL_RECEIVER | Default recipient for audit alerts | <admin@cladtek.com> |
| SMTP_SERVER | SMTP Relay/Server address | smtp.gmail.com |
| PORT | SMTP port (usually 587 for TLS) | 587 |

### 9.2 Docker Secrets (Sensitive Data)

These must be created as Secrets in Portainer. The system expects these to be available at `/run/secrets/`.

#### Infrastructure & Auth

`database_url`: Connection string (e.g., sqlite:////app/data/offboarding.db).
`secret_key`: Secure random string for JWT signing.

#### Active Directory (LDAP)

`ad_username`: Service account username.
`ad_password`: Service account password.
`ad_server`: Domain Controller IP or Hostname.
`ad_domain`: AD Domain (e.g., cladtek.local).
`ad_base_dn`: Search base DN (e.g., DC=cladtek,DC=local).
`disabled_ou`: Target OU for deactivated users.

#### Third-party Integrations

`intouch_url` & `intouch_token`: API credentials for InTouch system.
`email_password`: Password or App Password for the SMTP server.
`turnstile_a_url` & `turnstile_a_session`: Credentials for ControlID/Turnstile A.
`turnstile_b_url` & `turnstile_b_session`: Credentials for ControlID/Turnstile B.

## 10. Status

Current version: v1.0.0
Environment: Internal Production (Local Network)
