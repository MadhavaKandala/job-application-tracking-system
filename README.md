# Job Application Tracking System (ATS) - Backend API

A robust, production-ready backend system for an Applicant Tracking System (ATS) built with **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**. This system manages complex job application workflows with comprehensive role-based access control (RBAC), state machine transitions, and asynchronous email notifications.

## Features

- **RESTful API** with JWT authentication
- **Role-Based Access Control (RBAC)** for Candidates, Recruiters, and Hiring Managers
- **State Machine Workflow** enforcing valid application stage transitions
- **Asynchronous Email Notifications** via Celery background jobs
- **Comprehensive Audit Trail** with ApplicationHistory logging
- **Database Transactions** for data consistency
- **Environment Variable Configuration** for security
- **Complete API Documentation** with examples

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+
- **Job Queue**: Redis 7.0+ + Celery 5.3+
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic V2
- **Email**: SendGrid
- **Testing**: pytest

## Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app & routes registration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # Database connection & session
│   ├── config.py               # Configuration from env vars
│   ├── deps.py                 # Dependency injection (auth, RBAC)
│   ├── routers/
│   │   ├── auth.py             # Auth endpoints (register, login)
│   │   ├── jobs.py             # Job CRUD endpoints
│   │   └── applications.py     # Application management endpoints
│   ├── services/
│   │   ├── auth_service.py     # JWT generation & validation
│   │   ├── rbac_service.py     # RBAC logic
│   │   ├── workflow_service.py # State machine & transitions
│   │   └── email_tasks.py      # Celery tasks
│   └── utils/
│       ├── security.py         # Password hashing
│       └── errors.py           # Custom exceptions
├── migrations/                 # Alembic DB migrations
├── tests/                      # Unit & integration tests
├── docker-compose.yml          # PostgreSQL, Redis setup
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md
```

## Database Schema (ERD)

### Tables

**User**
- `id` (PK): UUID
- `email` (UNIQUE): String
- `password_hash`: String
- `role`: Enum (candidate, recruiter, hiring_manager)
- `company_id` (FK): UUID (nullable)
- `created_at`: DateTime

**Company**
- `id` (PK): UUID
- `name`: String
- `created_at`: DateTime

**Job**
- `id` (PK): UUID
- `company_id` (FK): UUID
- `title`: String
- `description`: Text
- `status`: Enum (open, closed)
- `created_by` (FK): UUID (Recruiter)
- `created_at`: DateTime

**Application**
- `id` (PK): UUID
- `job_id` (FK): UUID
- `candidate_id` (FK): UUID
- `stage`: Enum (Applied, Screening, Interview, Offer, Hired, Rejected)
- `created_at`: DateTime
- `updated_at`: DateTime

**ApplicationHistory**
- `id` (PK): UUID
- `application_id` (FK): UUID
- `old_stage`: Enum
- `new_stage`: Enum
- `changed_by` (FK): UUID (User)
- `changed_at`: DateTime

## Application Workflow

Valid state transitions:

```
Applied → Screening → Interview → Offer → Hired
   ↓         ↓           ↓         ↓        ↓
 Rejected ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← 
```

- Normal progression: `Applied → Screening → Interview → Offer → Hired`
- Rejection allowed from any non-terminal state
- Invalid transitions (e.g., `Applied → Offer`) are blocked
- State changes are logged in `ApplicationHistory`

## API Endpoints

### Authentication

**POST /auth/register**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "role": "candidate",
  "company_id": "<UUID>"  # Required only for recruiter/hiring_manager
}
```

**POST /auth/login**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

Response:
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user": {
    "id": "<UUID>",
    "email": "user@example.com",
    "role": "candidate"
  }
}
```

### Jobs

**POST /api/jobs** (Recruiter only)
```json
{
  "title": "Senior Backend Developer",
  "description": "Job description here",
  "status": "open"
}
```

**GET /api/jobs**
Get all jobs (paginated)

**GET /api/jobs/{job_id}**
Get job details

**PUT /api/jobs/{job_id}** (Recruiter of company)
Update job

**DELETE /api/jobs/{job_id}** (Recruiter of company)
Delete job

### Applications

**POST /api/jobs/{job_id}/applications** (Candidate only)
Candidate applies for a job
- Triggers async email to candidate
- Triggers async email to recruiter

**PATCH /api/applications/{app_id}/stage** (Recruiter/HiringManager)
```json
{
  "new_stage": "Screening"
}
```
- Validates state transition
- Updates application
- Creates ApplicationHistory entry
- Triggers async email to candidate

**GET /api/applications/{app_id}** (Authorized users)
View application details
- Candidate: own applications
- Recruiter/HiringManager: applications for their company's jobs

**GET /api/jobs/{job_id}/applications** (Recruiter/HiringManager)
List applications with stage filter
- Query: `?stage=Screening` (optional)

**GET /api/me/applications** (Candidate)
Candidate's applications with current status

## RBAC Matrix

| Resource/Action | Candidate | Recruiter | HiringManager |
|---|---|---|---|
| Apply for job | ✓ | ✗ | ✗ |
| View own apps | ✓ | ✗ | ✗ |
| Create job | ✗ | ✓ (own company) | ✗ |
| View job apps | ✗ | ✓ (own company) | ✓ (own company) |
| Update app stage | ✗ | ✓ (own company) | ✓ (assigned) |
| View app details | ✓ (own) | ✓ (own company) | ✓ (own company) |

## Async Email Workflow

**Celery Tasks**

1. **send_application_submitted_email(application_id)**
   - Triggered when candidate submits application
   - To: Candidate
   - Subject: "Application Received"

2. **send_stage_changed_email(application_id, new_stage)**
   - Triggered on stage update
   - To: Candidate
   - Subject: "Application Status Updated"

3. **send_new_application_email(job_id, application_id)**
   - Triggered on new application
   - To: Job's recruiter
   - Subject: "New Application Received"

## Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 7.0+
- Docker & Docker Compose (recommended)

### Local Setup

1. **Clone repository**
```bash
git clone https://github.com/MadhavaKandala/job-application-tracking-system.git
cd job-application-tracking-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start PostgreSQL & Redis (Docker)**
```bash
docker-compose up -d
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Start FastAPI server**
```bash
uvicorn app.main:app --reload
```

8. **Start Celery worker** (in another terminal)
```bash
celery -A app.services.email_tasks worker --loglevel=info
```

### Environment Variables (.env)

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ats_db

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@ats.example.com

# Environment
ENVIRONMENT=development
DEBUG=True
```

## API Testing with Postman

1. Import the included `ats-api.postman_collection.json`
2. Set Postman environment variables (base_url, token, etc.)
3. Run the test collection

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_workflow.py

# Verbose output
pytest -v
```

## Key Implementation Details

### State Machine Service

The `workflow_service.py` implements the state machine logic:

- Validates transitions
- Prevents invalid state jumps
- Ensures "Rejected" is only reachable from non-terminal states
- Returns clear error messages

### RBAC Middleware

The `deps.py` provides:

- JWT token verification
- User role extraction
- Company-level authorization
- Route-level permission decorators

### Transaction Safety

When updating application stage:

1. Begin transaction
2. Update Application.stage
3. Insert ApplicationHistory record
4. Commit transaction
5. Enqueue email task (after commit)

## Security Best Practices

✅ Passwords hashed with bcrypt
✅ JWT tokens with expiration
✅ HTTPS enforced in production
✅ Environment variables for secrets
✅ SQL injection protection via ORM
✅ CORS properly configured
✅ Rate limiting (to be added)
✅ Input validation with Pydantic

## Deployment

The application can be deployed to:
- **Railway.app**: Recommended for quick setup
- **Render**: Database + Redis + API hosting
- **AWS**: EC2 + RDS + ElastiCache
- **DigitalOcean**: App Platform + Managed Database

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
