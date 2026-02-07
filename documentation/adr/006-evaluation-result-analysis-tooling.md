# ADR-006: Human Data Annotation for Minute Summaries (Rubric-Aligned)

## Status

{Draft | Proposed | Accepted | Rejected | Superseded}

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

Minute generates summaries from meeting transcripts, and we evaluate summary quality using an LLM-as-judge rubric (e.g., faithfulness, coverage, conciseness, coherence). To trust and improve LLM-as-judge scoring and prompt optimisation, we need a human annotation process that:

- Collects human scores aligned to the same rubric dimensions.
- Enables comparing human vs machine scores to measure correlation and calibration.
- Produces a reusable evaluation dataset for judge prompt iteration and DSPy optimisation.
- Supports periodic review (ongoing audits) in addition to one-off dataset creation.

We also need an annotation tool/interface that makes the process efficient, consistent, and auditable.

## Considered Options

- Ad-hoc spreadsheet / offline review
- Lightweight internal web annotation tool (preferred)
- Full-featured third-party labeling platform
- Human-in-the-loop review embedded into the product UI

## Decision Outcome

{Title of Option X}, because {summary justification / rationale}.

## Pros and Cons of the Options

### Ad-hoc spreadsheet / offline review

This approach exports transcripts/summaries to a spreadsheet or document and asks reviewers to provide scores.

- Good, because it is fast to start and requires minimal engineering.
- Good, because it is flexible for early exploration.
- Bad, because it is hard to enforce consistency and required fields.
- Bad, because it is difficult to version, audit, and reproduce.
- Bad, because it is not well-suited for periodic reviews and assignment workflows.

### Lightweight internal web annotation tool (preferred)

This approach provides a simple UI where a reviewer can view:

- Transcript (with speaker attribution and timestamps if available)
- Candidate summary (produced by Minute)
- Optional reference summary (if present)
- Optional LLM-as-judge output (scores + rationale) for comparison (configurable)

The reviewer then records rubric-aligned annotations.

Recommended rubric dimensions (aligned to LLM-as-judge):

- Faithfulness
- Coverage
- Conciseness
- Coherence

Annotation depth options (configurable per project or per batch):

- Score-only (e.g., 1–5) per dimension
- Score + short rationale per dimension
- Score + rationale + evidence spans (quote transcript snippets that justify score)
- Binary flags for critical failures (e.g., hallucination present, incorrect action item owner)

Operational features the tool should support:

- Queue / assignment (who reviews what)
- Double annotation on a subset for inter-annotator agreement
- Conflict resolution / adjudication workflow
- Reviewer guidelines embedded in the UI (rubric definitions + examples)
- Change history (who edited what, when)
- Export to a structured format usable for evaluation/optimisation

- Good, because it enforces a consistent schema aligned to evaluation needs.
- Good, because it supports periodic review and sampling.
- Good, because it can integrate with existing eval outputs (runs/results) and reuse IDs.
- Bad, because it requires engineering effort and ongoing maintenance.
- Neutral, because scope can be kept small initially and expanded over time.

### Full-featured third-party labeling platform

This approach uses an off-the-shelf labeling tool with workflows, QA, and analytics.

- Good, because it provides mature workflow management and QA.
- Good, because it can scale to larger annotation programs.
- Bad, because it may be costly and require integration work.
- Bad, because it can be hard to customize for rubric-specific UX (e.g., evidence spans, side-by-side judge comparisons).
- Neutral, because it can be adopted later once requirements stabilize.

### Human-in-the-loop review embedded into the product UI

This approach asks end users to provide feedback on summaries within the product.

- Good, because it captures real user judgment and real meeting distributions.
- Good, because it can run continuously, with feedback from real usage over time.
- Bad, because it requires strong UX design and careful sampling to avoid bias.
- Bad, because feedback may be noisy and not rubric-consistent without training.
- Neutral, because it can complement a dedicated annotation workflow.

## More Information

### Correlation and calibration

To validate LLM-as-judge, we should track:

- Correlation between human and LLM scores per dimension.
- Calibration curves (where judges are systematically high/low).
- Disagreement analysis by category (e.g., numbers, attribution, negation).

This can be used to:

- Decide whether the judge is reliable enough for optimisation.
- Identify rubric dimensions that need prompt refinement.
- Build a gold/anchor set for regression evaluation.

### Periodic reviews

In addition to initial dataset creation, the same tool should support ongoing audits:

- Sample recent production-like outputs periodically.
- Run human review on a fixed budget (e.g., N items per week).
- Track trends over time and across model/prompt versions.

### Data storage, versioning, and export

The annotations should be stored with:

- Stable identifiers (example_id, run_id, prompt/version identifiers)
- The exact transcript and candidate summary version shown to the reviewer
- Annotation schema version
- Reviewer metadata (anonymized as needed)

Exports should support:

- Evaluation datasets for LLM-as-judge prompt iteration
- Training/validation splits for DSPy optimisation and held-out testing

Signoff, correct consent, data agreement will be required for:

- Any use of production/user transcripts in labeling workflows
- Human reviewer access controls and data retention policies (if any)
- Third-party labeling vendor usage
