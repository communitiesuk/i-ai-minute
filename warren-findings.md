# Warren's Findings - Minute Application Analysis

## Overview

This document summarizes key findings about the Minute application's architecture, authentication system, and AI service integrations based on codebase analysis.

## Local Development Authentication

The application implements a **bypass mechanism** for local development that automatically logs you in without requiring real credentials:

### How Local Auth Works

1. **Automatic Test User**: When `ENVIRONMENT=local`, the frontend uses a hardcoded JWT token containing fake user credentials (`test@test.co.uk` with role `minute`)

2. **Signature Verification Disabled**: The `DISABLE_AUTH_SIGNATURE_VERIFICATION=true` environment variable tells both frontend and backend to skip cryptographic verification of JWT tokens

3. **Role-Based Access**: The application checks if the user has the `minute` role (matching the `REPO=minute` environment variable) to grant access

### Production vs Local Auth

- **Production**: Uses AWS Load Balancer OIDC integration with Keycloak for real authentication
- **Local**: Uses test JWT + disabled verification for development convenience

## AI Services Architecture

The application requires **two types of AI services** to function:

### 1. Transcription Services (Choose One)

**Azure Speech-to-Text** (Recommended for local dev)
- Service: `azure_stt_synchronous` or `azure_stt_batch`
- Requirements: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
- Best for: Quick setup, supports real-time and batch processing

**AWS Transcribe**
- Service: `aws_transcribe`
- Requirements: AWS credentials, S3 bucket
- Best for: Production environments already using AWS

### 2. LLM Services (Choose One)

**Google Gemini** (Default/Recommended)
- Provider: `LLM_PROVIDER=gemini`
- Model: `gemini-2.0-flash` or `gemini-2.5-flash`
- Requirements: Google Cloud project, service account JSON
- Best for: Government/enterprise use cases (as evidenced by codebase focus)

**Azure OpenAI**
- Provider: `LLM_PROVIDER=openai`
- Models: GPT-4, etc.
- Requirements: Azure OpenAI subscription, deployment name
- Best for: Organizations already using Azure ecosystem

## Service Configuration Strategy

The application uses a **modular approach** where you can mix and match:
- Azure transcription + Google Gemini LLM
- AWS transcription + Azure OpenAI LLM
- Any combination based on your existing cloud infrastructure

## Local Development Dependencies

For local development, the application uses:
- **LocalStack**: Emulates AWS services (S3, SQS) locally
- **Docker Compose**: Orchestrates all services with hot reload
- **PostgreSQL**: Database (containerized)
- **Next.js + FastAPI**: Frontend and backend with auto-generated API clients

## Key Insights

1. **Authentication is completely bypassed** for local development - you don't need any real auth provider setup
2. **You must have at least one transcription service** and **one LLM service** configured for the app to be functional
3. **LocalStack handles infrastructure** - no need for real AWS accounts for storage/queues during development
4. **The application is designed for government use** - evidenced by templates for Cabinet meetings, planning committees, etc.
5. **Multi-cloud ready** - designed to work across AWS, Azure, and Google Cloud platforms

## Minimum Setup for Local Testing

To get the application running locally, you need:
1. Copy `.env.minimal` to `.env`
2. Add credentials for one transcription service (Azure Speech recommended)
3. Add credentials for one LLM service (Google Gemini recommended)
4. Run `make run`

The authentication will work automatically without any additional setup.