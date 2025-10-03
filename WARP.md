# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

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

**Minute** is an AI-powered meeting transcription and minute generation application with a microservices architecture:

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
- **Templates**: Government-specific minute formats (Cabinet, Planning Committee, etc.)

## Key Development Patterns

### Template System
Templates are located in `common/templates/` and automatically discovered. Implement either `SimpleTemplate` or `SectionTemplate` protocols for custom meeting formats.

### Configuration
All settings are centralized in `common/settings.py` with environment variable overrides. Use `.env` for local development.

### Testing Strategy
- Unit tests in `tests/` directory
- E2E queue processing tests require preprocessed `.json` files in `.data/` directory
- Paid API tests gated behind `ALLOW_TESTS_TO_ACCESS_PAID_APIS` flag

### Development Environment
Uses Docker Compose with file watching for hot reload. The `--watch` flag syncs local changes to containers and restarts services as needed.

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

The application is designed for cloud deployment with Terraform configurations. Architecture diagrams are available in the repository root showing the AWS/Azure deployment topology.

## Troubleshooting

### Common Docker Issues

**"base64: invalid input" error**: Occurs when `GOOGLE_APPLICATION_CREDENTIALS_BASE64` is set to an invalid value. Either remove this environment variable or set it to a valid base64-encoded Google service account JSON.

**Sentry DSN error**: If you see `BadDsn: Unsupported scheme ''`, set `SENTRY_DSN=` (empty) in your `.env` file unless you have a valid Sentry DSN.

**Services not starting**: Check individual container logs:
```bash
docker compose logs backend --tail=50
docker compose logs frontend --tail=50
docker compose logs worker --tail=50
```

**Health check endpoints**:
- Backend: http://localhost:8080/healthcheck
- Frontend: http://localhost:3000
- Worker Ray Dashboard: http://localhost:8265
