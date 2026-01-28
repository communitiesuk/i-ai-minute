# ADR-013: Evaluation Alerting

## Status

Proposed

Date of decision: 2025-01-27

## Context and Problem Statement

Evaluations need to surface issues to the right people at the right time. We need to determine how to alert stakeholders when evaluations fail or detect regressions, balancing timely notification with alert fatigue and infrastructure complexity.

## Considered Options

* CI/CD Native Alerting [preferred]
* Dedicated Monitoring and Alerting Systems
* No Dedicated Alerting Infrastructure

## Decision Outcome

CI/CD Native Alerting, because it integrates seamlessly with existing workflows and requires no additional infrastructure.

## Pros and Cons of the Options

### CI/CD Native Alerting [preferred]

Use the CI/CD platform's built-in notification system (e.g., GitHub Actions status checks, pipeline failure notifications).

* Good, because integrates seamlessly with existing workflows.
* Good, because requires no additional infrastructure.
* Bad, because insights only reach people with repository access.
* Bad, because scheduled evaluations may not reach the right people.

### Dedicated Monitoring and Alerting Systems

Send evaluation results to dedicated monitoring platforms (e.g., CloudWatch, Datadog, PagerDuty) for alerting.

* Good, because aligns with production monitoring infrastructure.
* Good, because reaches people regardless of GitHub access.
* Bad, because requires additional infrastructure setup and access management.
* Bad, because it may require procuring additional subscriptions.

### No Dedicated Alerting Infrastructure

Store evaluation results without implementing automated alerting, relying on manual review of stored results.

* Good, because fine-tuning thresholds for AI systems is complex.
* Good, because avoids alert fatigue.
* Bad, because major issues may go unnoticed.

## Sign-off Required

### Dedicated Monitoring and Alerting Systems

Using dedicated monitoring platforms requires sign-off for:

* Subscription costs: Additional monitoring platform licenses or usage fees.
* Integration effort: Development time to integrate evaluation results with monitoring systems.
* Access management: Managing credentials and permissions for monitoring platforms.
