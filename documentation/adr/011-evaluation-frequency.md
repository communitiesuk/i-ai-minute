# ADR-011: Evaluation Frequency

## Status

Proposed

Date of decision: 2025-01-27

## Context and Problem Statement

When should evaluations run throughout the development and deployment lifecycle? We need to balance early detection of developer errors, prevention of production regressions, and monitoring for upstream provider changes.

## Considered Options

* Local checks with production models
* Local checks with local models
* Commit checks
* Pre-deployment checks
* Scheduled production monitoring
* Combination of multiple stages [preferred]

## Decision Outcome

Combination of multiple stages, because it balances early detection with comprehensive validation, addresses different failure modes across the lifecycle, and enables rapid iteration while maintaining quality.

## Pros and Cons of the Options

### Local checks with production models

Run evaluations on the developer's local machine using the same models as production, requiring direct access to the AI infrastructure.

* Good, because it faciliates issues being spotted extremely early.
* Good, because results are directly comparable with production.
* Bad, because requires environment separation or dedicated service.
* Bad, because increases AI API costs.
* Bad, because it's harder to facilitate an enforcement mechanism.

### Local checks with local models

Run evaluations on the developer's local machine using locally-hosted models instead of production models.

* Good, because it faciliates issues being spotted extremely early.
* Good, because avoids additional AI API costs.
* Bad, because requires hardware capable of running AI models.
* Bad, because results not comparable with production, which hinders regression tracking.
* Bad, because it's harder to facilitate an enforcement mechanism.

### Commit checks

Run evaluations when a pull request is created or updated, before code is merged into the main branch.

* Good, because makes reverting easier than post-merge fixes.
* Good, because provides clear quality gate before integration.
* Good, because balances thoroughness with resource efficiency.
* Bad, because adds strain on CI/CD infrastructure.
* Bad, because may significantly slow down PR reviews.

### Pre-deployment checks

Run thorough evaluations before changes are deployed to production, after code has been merged.

* Good, because prevents regressions from reaching production.
* Good, because can run comprehensive evaluations without blocking development.
* Good, because catches issues specific to production-like environments.
* Bad, because issues require more effort to fix than earlier detection.
* Bad, because may delay deployments.

### Scheduled production monitoring

Run evaluations on a regular cadence (e.g., daily, weekly) against the production system without any code changes.

* Good, because detects regressions from upstream provider changes.
* Good, because establishes reference points for quality over time.
* Good, because identifies gradual degradation missed by deployment checks.
* Bad, because detects issues after they may have affected users.
* Bad, because incurs ongoing resource costs.

### Combination of multiple stages [preferred]

Implement evaluations at multiple stages with different levels of thoroughness: local checks for rapid iteration, commit checks for quality gates, pre-deployment checks for final validation, and scheduled monitoring for production health. It's potentially beneficial to not use local-models in this options so that comparisons are more direct.

* Good, because balances early detection with comprehensive validation.
* Good, because addresses different failure modes across the lifecycle.
* Good, because enables different evaluation strategies per stage.
* Good, because enables rapid iteration while maintaining quality.
* Bad, because increases system complexity significantly.
* Bad, because it has by far the largest AI API cost.

## Sign-off Required

### Local checks with production models

Enabling local evaluation checks with production models requires sign-off for:

* Increased API usage and direct access: Costs increase proportional to developers running evaluations locally.
* Environment separation or dedicated service: Requires environment separation or dedicated service for evaluation requests.

### Local checks with local models

Enabling local evaluation checks with local models requires sign-off for:

* Hardware requirements: All developers need capable hardware; may require upgrades.

### CI/CD evaluation stages (commit-level, pre-deployment)

Finer-grained evaluation stages incur higher costs and require sign-off for:

* Increased API usage: Each stage runs evaluations, multiplying costs.
* CI/CD resource usage: Additional pipeline stages consume runner time.

### Scheduled production monitoring

Regular production monitoring requires sign-off for:

* Ongoing API costs: Evaluations run continuously regardless of changes.
