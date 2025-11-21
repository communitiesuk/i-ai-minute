# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this
repository.

## Common Development Commands

### Environment Setup

```bash
# Copy environment file and configure
cp .env.example .env
# Edit .env with your API keys and configuration

# Install dependencies
make install
```

### Running the Application

```bash
# Run full application with hot reload (recommended for development)
make run_watch

# Run full application in background
make run

# Stop all services
make stop

# Individual service startup (for debugging)
make run_frontend    # Frontend at http://localhost:3000
make run_backend     # Backend API at http://localhost:8080
make run_worker      # Worker service for processing
```

### Testing

```bash
# Run all tests
make test

# Run tests with paid API access (for LLM evaluations)
ALLOW_TESTS_TO_ACCESS_PAID_APIS=1 make test

# Run specific test file
poetry run pytest tests/test_templates.py

# Run pre-commit checks
make run-pre-commit
```

### Code Quality

```bash
# Format and lint Python code
poetry run ruff format .
poetry run ruff check .

# Frontend linting and formatting
cd frontend && npm run lint
cd frontend && npm run prettier:fix

# Generate API types for frontend
make generate_api_types
```

## Architecture Overview

**Minute** is an AI-powered meeting transcription and minute generation
application with a microservices architecture:

### Core Components

1. **Frontend** (`frontend/`): Next.js application with TypeScript
   - Uses auto-generated API client from OpenAPI spec
   - Radix UI components with Tailwind CSS
   - Real-time job status tracking
2. **Backend** (`backend/`): FastAPI service
   - Handles HTTP requests and database operations
   - Queues long-running tasks (transcription, LLM processing)
   - Auto-generates OpenAPI documentation at `/api/openapi.json`
3. **Worker** (`worker/`): Background processing service
   - Uses Ray for distributed computing
   - Handles transcription via Azure Speech/AWS Transcribe
   - LLM processing for minute generation
   - Dashboard available at http://localhost:8265
4. **Common** (`common/`): Shared utilities and configuration
   - Database models and migrations (SQLModel/Alembic)
   - Settings management with Pydantic
   - Template system for different meeting types

### Database & Storage

- **PostgreSQL**: Primary database with async SQLModel/SQLAlchemy
- **S3/Azure Blob**: File storage for audio uploads and processed files
- **SQS/Azure Service Bus**: Message queues for job processing
- **LocalStack**: Local AWS services emulation for development

### AI Services Integration

- **Transcription**: Azure Speech-to-Text, AWS Transcribe (configurable)
- **LLM**: Azure OpenAI, Google Gemini (configurable via `LLM_PROVIDER`)
- **Templates**: Government-specific minute formats (Cabinet, Planning
  Committee, etc.)

## Key Development Patterns

### Template System

Templates are located in `common/templates/` and automatically discovered.
Implement either `SimpleTemplate` or `SectionTemplate` protocols for custom
meeting formats.

- `SimpleTemplate`: For straightforward minute generation with a single prompt
- `SectionTemplate`: For structured, multi-section minutes with detailed
  content per section
- Both support optional citation inclusion via `citations_required` attribute

### Configuration

All settings are centralized in `common/settings.py` with environment variable
overrides. Use `.env` for local development.

- Settings use Pydantic for validation and type safety
- Multi-cloud configuration via service name selectors (e.g.
  `STORAGE_SERVICE_NAME`, `QUEUE_SERVICE_NAME`)
- LLM configuration supports both "fast" and "best" model tiers for different
  task complexities

### Multi-Cloud Abstraction

The codebase uses abstraction layers in `common/services/` to support multiple
cloud providers:

- **Storage**: `storage_services/` (S3, Azure Blob, or local filesystem)
- **Queues**: `queue_services/` (SQS or Azure Service Bus)
- **Transcription**: `transcription_services/` (Azure STT, AWS Transcribe)

Select providers via environment variables in `.env`.

### Database Migrations

Database schema changes use Alembic:

```bash
# Generate a new migration after modifying models in common/database/
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1
```

Migrations are in `alembic/versions/`. Models are defined in
`common/database/postgres_models.py` using SQLModel.

### API Type Generation

The frontend uses auto-generated TypeScript types from the backend's OpenAPI
spec:

1. Backend must be running (exposes `/api/openapi.json`)
2. Run `make generate_api_types` or `cd frontend && npm run openapi-ts`
3. Generated types appear in `frontend/lib/client/` (via Hey API)

Regenerate types whenever backend API changes.

### Testing Strategy

- Unit tests in `tests/` directory
- E2E queue processing tests require preprocessed `.json` files in `.data/`
  directory
- Test marks in `tests/marks.py`:
  - `@costs_money`: Requires `ALLOW_TESTS_TO_ACCESS_PAID_APIS=1`
  - `@acceptance_test`: Requires `RUN_ACCEPTANCE_TESTS=1`
  - `@requires_audio_data`: Needs audio files in `.data/test_audio/normal/`

### Development Environment

Uses Docker Compose with file watching for hot reload. The `--watch` flag syncs
local changes to containers and restarts services as needed.

### Worker Monitoring

The worker service uses Ray for distributed task processing. Monitor worker
status via:

- **Ray Dashboard**: http://localhost:8265 (when worker is running)
- Shows active tasks, resource utilization, logs, and task execution timeline
- Worker container requires 2+ CPUs and 4GB shared memory (`shm_size`)

## Project Structure Notes

- Poetry for Python dependency management
- Pre-commit hooks for code quality (Ruff, secrets detection)
- Alembic for database migrations
- Sentry integration for error tracking
- PostHog for analytics and feature flags
- Multi-cloud deployment support (AWS/Azure)

## Environment Variables

Key variables for local development (see `.env.example` for full list):

- `TRANSCRIPTION_SERVICES`: Array of transcription service names
- `LLM_PROVIDER`: "openai" or "gemini"
- `STORAGE_SERVICE_NAME`: "s3" or "azure-blob"
- `QUEUE_SERVICE_NAME`: "sqs" or "azure-service-bus"
- `USE_LOCALSTACK`: Enable LocalStack for local AWS emulation

## Deployment

The application is designed for cloud deployment with Terraform configurations.
Architecture diagrams are available in the repository root showing the AWS/Azure
deployment topology.

## Troubleshooting

### Common Docker Issues

**"base64: invalid input" error**: Occurs when
`GOOGLE_APPLICATION_CREDENTIALS_BASE64` is set to an invalid value. Either
remove this environment variable or set it to a valid base64-encoded Google
service account JSON.

**Sentry DSN error**: If you see `BadDsn: Unsupported scheme ''`, set
`SENTRY_DSN=` (empty) in your `.env` file unless you have a valid Sentry DSN.

**LocalStack not ready**: If services fail to start, ensure LocalStack
healthcheck passes. Check logs with `docker compose logs localstack`. The
`localstack-setup.sh` script creates required SQS queues on startup.

**Services not starting**: Check individual container logs:

```bash
docker compose logs backend --tail=50
docker compose logs frontend --tail=50
docker compose logs worker --tail=50
```

**Worker Ray errors**: If worker fails to initialize, check Ray dashboard at
http://localhost:8265 and verify worker container has sufficient resources
(2 CPUs, 4GB shm_size).

**Health check endpoints**:

- Backend: http://localhost:8080/healthcheck
- Frontend: http://localhost:3000
- Worker Ray Dashboard: http://localhost:8265
- Database: `docker compose exec db pg_isready -d minute_db`
