# i-ai-minute Codebase Overview

## Architecture

The application follows a microservices architecture with separate frontend,
backend API, and worker services orchestrated via Docker Compose. It supports
deployment on AWS/Azure with configurable cloud services.

## Audio to output process

1. User uploads 30-minute meeting recording
2. API immediately returns { id: "123", status: "AWAITING_START" }
3. Worker picks up transcription job from queue
4. Worker updates DB: status: "IN_PROGRESS"
5. Frontend polls API, shows progress spinner
6. X minutes later: transcription completes
7. Worker automatically queues next job: TaskType.MINUTE
8. Second worker generates meeting minutes from transcript
9. DB updated: status: "COMPLETED"
10. Frontend shows final results

## Technology Stack

### Frontend (`/frontend/`)

- **Framework**: Next.js 14 with TypeScript
- **UI Components**: Radix UI primitives with Tailwind CSS
- **Rich Text Editor**: Tiptap for minute editing
- **State Management**: TanStack Query for API state
- **API Client**: Auto-generated using Hey API from OpenAPI specs
- **Analytics**: PostHog integration
- **Error Tracking**: Sentry
- **File Handling**: React Dropzone, file-saver for downloads

### Backend API (`/backend/`)

- **Framework**: FastAPI (Python 3.12)
- **Authentication**: OAuth2 with JWT
- **API Documentation**: Auto-generated OpenAPI/Swagger
- **Middleware**: CORS, Sentry integration
- **Job Queuing**: Async task dispatch to worker services

### Worker Service (`/worker/`)

- **Task Processing**: Ray framework for distributed computing
- **Audio Processing**: FFmpeg integration via ffmpeg-python
- **Transcription Services**:
  - Azure Speech-to-Text
  - AWS Transcribe (configurable)
- **LLM Integration**:
  - Google Gemini (default: gemini-2.0-flash)
  - Azure OpenAI
- **Audio Format Support**: Multi-format conversion and optimization

### Shared Components (`/common/`)

- **Database**: SQLAlchemy with async PostgreSQL support
- **Settings Management**: Pydantic Settings with environment configuration
- **Audio Processing**: Speaker detection, format conversion
- **Templates**: Extensible meeting template system
- **Services**: Transcription handler, minute generation, PostHog client
- **LLM Client**: Abstracted client supporting multiple providers

### Database Layer

- **ORM**: SQLModel with PostgreSQL
- **Migrations**: Alembic for schema management
- **Models**: Transcriptions, minutes, recordings, job states, chat history
- **Cleanup**: Automated data retention scheduling

### Infrastructure (`/terraform/`)

- **Platform**: AWS-focused with Azure abstractions
- **Services**: ECS, RDS, S3, SQS, Load Balancer
- **IAM**: Role-based access control
- **Secrets**: AWS Systems Manager Parameter Store

## Key Features

### Multi-Cloud Support

- **Storage**: S3 or Azure Blob Storage
- **Queues**: SQS or Azure Service Bus
- **Transcription**: Azure Speech-to-Text, AWS Transcribe
- **LLM**: Google Gemini, Azure OpenAI

### Template System

Extensible meeting minute templates for:

- Cabinet meetings
- Planning committees
- Care assessments
- General-purpose meetings

### Local development

- **Containerization**: Full Docker Compose stack
- **Local Services**: LocalStack for AWS service emulation
- **Development Tools**: Hot reload, file watching
- **Testing**: pytest with async support, Playwright for E2E

### QA

- **Code Quality**: Ruff for linting/formatting, pre-commit hooks
- **Testing**: Unit tests, E2E tests, LLM evaluation tests
- **Security**: Bandit security scanning, secrets detection
- **Monitoring**: Sentry error tracking, PostHog analytics

## Configuration

Environment-driven configuration supporting:

- Multiple deployment environments (local, dev, preprod, prod)
- Configurable transcription/LLM providers
- Data retention policies
- Feature flags via PostHog
- Comprehensive cloud service settings

## Deployment

- **CI/CD**: GitHub Actions for build/test/deploy
- **Infrastructure**: Terraform for AWS resources
- **Container Registry**: ECR with automated image builds
- **Orchestration**: ECS with load balancing and auto-scaling

## Key tech reference

| Category                        | Technology            | Description                       | Link                                                                  |
| ------------------------------- | --------------------- | --------------------------------- | --------------------------------------------------------------------- |
| **Core Frameworks & Languages** | Next.js               | React-based full-stack framework  | https://nextjs.org/                                                   |
|                                 | FastAPI               | Modern Python web framework       | https://fastapi.tiangolo.com/                                         |
|                                 | Python                | Programming language              | https://www.python.org/                                               |
|                                 | TypeScript            | Typed JavaScript superset         | https://www.typescriptlang.org/                                       |
|                                 | React                 | UI library for web applications   | https://react.dev/                                                    |
| **AI & Machine Learning**       | Google Gemini         | AI model and platform             | https://gemini.google.com/                                            |
|                                 | Azure OpenAI          | Microsoft's OpenAI service        | https://azure.microsoft.com/en-us/products/ai-services/openai-service |
|                                 | Azure Speech Services | Speech-to-text and text-to-speech | https://azure.microsoft.com/en-us/products/ai-services/speech-to-text |
|                                 | Ray                   | Distributed computing framework   | https://www.ray.io/                                                   |
| **Data & Storage**              | PostgreSQL            | Open source relational database   | https://www.postgresql.org/                                           |
|                                 | SQLAlchemy            | Python SQL toolkit and ORM        | https://www.sqlalchemy.org/                                           |
|                                 | Alembic               | Database migration tool           | https://alembic.sqlalchemy.org/                                       |
|                                 | Amazon S3             | Object storage service            | https://aws.amazon.com/s3/                                            |
|                                 | Azure Blob Storage    | Cloud object storage              | https://azure.microsoft.com/en-us/products/storage/blobs              |
| **Infrastructure & DevOps**     | Docker                | Containerization platform         | https://www.docker.com/                                               |
|                                 | Terraform             | Infrastructure as code            | https://www.terraform.io/                                             |
|                                 | AWS ECS               | Container orchestration service   | https://aws.amazon.com/ecs/                                           |
|                                 | LocalStack            | Local cloud development           | https://localstack.cloud/                                             |
| **Development Tools**           | Poetry                | Python dependency management      | https://python-poetry.org/                                            |
|                                 | Ruff                  | Fast Python linter and formatter  | https://docs.astral.sh/ruff/                                          |
|                                 | pytest                | Python testing framework          | https://pytest.org/                                                   |
|                                 | Playwright            | End-to-end testing                | https://playwright.dev/                                               |
| **Monitoring & Analytics**      | Sentry                | Error tracking and performance    | https://sentry.io/                                                    |
|                                 | PostHog               | Product analytics platform        | https://posthog.com/                                                  |
| **UI & Styling**                | Tailwind CSS          | Utility-first CSS framework       | https://tailwindcss.com/                                              |
|                                 | Radix UI              | Low-level UI primitives           | https://www.radix-ui.com/                                             |
|                                 | Tiptap                | Rich text editor toolkit          | https://tiptap.dev/                                                   |
