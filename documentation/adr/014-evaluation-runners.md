# ADR-014: Evaluation Runners

## Status

Proposed

Date of decision: 2025-01-27

## Context and Problem Statement

Choice of execution infrastructure affects control, cost, and complexity. Since computational load is on external APIs, the execution environment mainly provides orchestration. However, if evaluations use sensitive data, the execution environment must provide strong isolation, access controls, and audit capabilities. We need to determine where evaluation workloads should run.

## Considered Options

* Standard CI/CD Runners
* Dedicated CI/CD Runners

## Decision Outcome

Dedicated CI/CD Runners, because they provide stronger isolation for sensitive data, enable stricter access controls and audit logging, and ensure data never touches shared infrastructure. While this adds infrastructure complexity, it better addresses security and compliance requirements for handling sensitive evaluation data.

## Pros and Cons of the Options

### Standard CI/CD Runners

Run evaluations on the CI/CD platform's default shared runners (e.g., GitHub Actions hosted runners).

* Good, because requires no additional infrastructure and management of resources.
* Good, because logs integrate naturally with CI/CD workflows.
* Bad, because limited control over environment and network access.
* Bad, because sensitive data may touch shared infrastructure or logs.

### Dedicated CI/CD Runners

Deploy dedicated runners specifically for evaluation workloads (e.g. self-hosted GitHub Actions runners).

* Good, because provides isolation with stricter access controls and audit logging.
* Good, because ensures sensitive data never touches shared infrastructure.
* Good, because provides control over secrets management and network policies.
* Bad, because requires infrastructure setup and maintenance.
* Bad, because adds complexity for orchestration and CI/CD integration.

## Sign-off Required

### Dedicated CI/CD Runners

Using dedicated runners requires sign-off for:

* Infrastructure costs: Compute resources for self-hosted runners.
* Maintenance overhead: Managing runner infrastructure, updates, and security.
* Network configuration: VPC setup and access controls if required.
