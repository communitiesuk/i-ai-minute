# ADR-010: Live System Monitoring

## Status

Accepted

Date of decision: 2026-01-16

## Context and Problem Statement

We need a monitoring approach that enables reliable request tracing, performance visibility, and operational insight across environments. The system currently logs exceptions and analytics but lacks the depth required for production-scale debugging and bottleneck identification. As traffic grows, it becomes increasingly difficult to trace individual requests, diagnose latency, and understand system behaviour. We must decide what monitoring data to capture, where to store it, how to structure the monitoring architecture, and how monitoring should differ across environments.

## Considered Options

- AWS Cloudwatch
- Grafana
- New Relic

## Decision Outcome

AWS Cloudwatch provides solutions for each concern. As AWS manages the majority of our infrastructure, we benefit from a high level of integration and low overhead.

## Current Status

- The system runs fully on AWS-managed infrastructure.
- Teams already use CloudWatch, Sentry, and existing logging patterns.

## Decision Aspects

### Aspect 1: Monitoring Architecture

What types of monitoring data should we capture to effectively trace requests and identify bottlenecks?

- A hybrid approach—AWS-native storage with curated dashboards—provides unified visibility without forcing all monitoring into a single tool or introducing unnecessary complexity.

### Aspect 2: Resource Logging

- AWS automatically provides SQS, ECS, S3, and Aurora metrics. These offer valuable insight into queue depth, compute pressure, storage usage, and throughput. They require minimal implementation effort.

### Aspect 3: Storage & Visualisation

- CloudWatch provides both resource metrics and application logs. Dashboards can unify views across services.

### Aspect 4: Environment Strategy

- A tiered model is preferred: verbose logging and no alerting in development, moderate monitoring in test, and full monitoring with alerts in production.

### Aspect 5: Additional Application Logging

- Extending application logs provides the most actionable visibility: request lifecycle tracing, AI service call metrics, slow queries, queue message lifecycle, authentication events, and more. This requires engineering effort but yields the clearest debugging path.

## Alternatives

Third party services such as Datadog, New Relic and Grafana offer benefits such as improved visualisation and allow aggregation from multiple sources. This also introduces additional overheads, such as:

- Cost of integration and maintenance
- Additional licensing fees
- Introduces a learning curve for team members unfamiliar with these platforms
- Time lost awaiting approval
- Addition of external dependencies to the present monitoring infrastructure

While the benefits may not provide adequate ROI at present and short-term scale.
