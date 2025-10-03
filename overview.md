# i-ai-minute Codebase Overview

## Project Purpose
**Minute** is an AI-powered application for automating meeting transcription and minute generation in the public sector. It transforms audio recordings into structured, professional government meeting minutes using multiple transcription services and LLM-powered summarization.

## Architecture
The application follows a microservices architecture with separate frontend, backend API, and worker services orchestrated via Docker Compose. It supports deployment on AWS/Azure with configurable cloud services.

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

### Development Environment
- **Containerization**: Full Docker Compose stack
- **Local Services**: LocalStack for AWS service emulation
- **Development Tools**: Hot reload, file watching
- **Testing**: pytest with async support, Playwright for E2E

### Quality Assurance
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

This codebase demonstrates modern full-stack architecture with AI integration, designed for government compliance and scalability requirements.