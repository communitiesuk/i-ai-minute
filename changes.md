# Changes made to get it working locally

## Frontend-Backend Proxy Issue

- Changed `.env` line 56: `SENTRY_DSN=placeholder` → `SENTRY_DSN=`

## Silence the posthog in-browser console warnings

- Changed `.env` line 57: `POSTHOG_API_KEY=<>` → `POSTHOG_API_KEY=`

## useStartTranscription s3 bucket 403 error

- Updated `common/services/storage_services/s3.py` to use LocalStack endpoint
  when `ENVIRONMENT=local`
- Fixed presigned URLs to replace docker hostname `localstack:4566` with
  `localhost:4566` for browser access
- Added S3 bucket creation and CORS configuration to `localstack-setup.sh`
