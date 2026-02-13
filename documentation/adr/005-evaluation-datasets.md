# ADR-005: Data Strategy for Minute Summarisation and LLM-as-Judge Evaluation

## Status

Accepted

Date of decision: 2026-01-16

## Context and Problem Statement

Minute generates summaries from meeting transcripts, and we evaluate summary quality using an LLM-as-judge rubric (e.g., faithfulness, coverage, conciseness, coherence). The usefulness of both the product prompts and the evaluation depends on having a dataset that is:

* Representative of real usage, high quality, and diverse.
* Representative of real transcription quality.
* Versioned and auditable.
* Able to expand as new use-cases are added.
* Able to include borderline/tricky cases that are disproportionately important for quality and safety.

We need a data strategy that supports:

* A good initial sample to start iterating quickly.
* A path to improve dataset quality/coverage over time.
* Synthetic, human, and hybrid data generation options.
* Dataset versioning and tracking how dataset shifts affect evaluation quality.

## Considered Options

* Human-only dataset (real examples)
* Synthetic-only dataset
* Hybrid dataset: real examples + synthetic augmentation (preferred)
* Separate datasets per use case (with shared core set)

## Decision Outcome

Hybrid dataset: real examples + synthetic augmentation, with heavy bias towards human-annotated data because we are unlikely to be able to achieve human-only dataset. Development of a hybrid method creates smaller burden on data collection and annotation - our capacity to do this is limited. Down the line the ability to create synthetic data will expand our capability to test edge cases and new use cases.

## Pros and Cons of the Options

### Human-only dataset (real examples)

This approach uses only human-collected meeting transcripts (or approved real recordings/transcripts) with human-written reference summaries and/or human rubric labels.

* Good, because it is representative of real user distributions and failure modes.
* Good, because it captures natural speech patterns, disfluencies, and real meeting structure.
* Bad, because it is expensive and slow to collect and label.
* Bad, because it has privacy/compliance constraints that can limit sharing and tooling.
* Bad, because it may under-represent rare but important edge cases unless explicitly curated.
* Neutral, because its value depends heavily on consistent annotation guidelines and QA.

### Synthetic-only dataset

This approach generates transcripts and/or summaries synthetically (e.g., using an LLM to create realistic meeting scenarios) and uses generated references and/or rubric labels.

* Good, because it is fast to scale and cheap to expand across many scenarios.
* Good, because it makes it easy to target specific patterns (numbers, negation, action items, attribution).
* Bad, because it can be unrepresentative and lead to overfitting on synthetic style.
* Bad, because it can hide real-world transcription artifacts and messy meeting dynamics.
* Bad, because synthetic labels may encode judge/model biases and reduce trust in evaluation.
* Neutral, because it can still be valuable for regression and targeted stress testing.

### Hybrid dataset: real examples + synthetic augmentation (preferred)

This approach starts from a representative sample of real examples and augments it with synthetic and curated edge cases. The synthetic portion is used primarily to:

* Increase coverage of rare or difficult patterns.
* Expand to new use cases quickly.
* Maintain a stable regression suite.

The real portion is used to:

* Anchor evaluation to actual production distributions.
* Detect regressions that only appear in real meeting data.

* Good, because it balances representativeness with scalability.
* Good, because it supports rapid iteration while still grounding quality in reality.
* Good, because it allows explicit tracking of which failures are “real-world” vs “stress tests”.
* Bad, because it increases complexity (multiple sources, differing label quality).
* Bad, because it requires careful dataset versioning and subset definitions.
* Neutral, because it still requires periodic human audits to ensure evaluation remains meaningful.

### Separate datasets per use case (with shared core set)

This approach maintains:

* A shared “core” dataset that represents common usage.
* Additional datasets per use case (e.g., sales call, standup, interview, support call), each with tailored tricky cases.

* Good, because it prevents a single blended dataset from hiding use-case-specific regressions.
* Good, because it scales as new use cases are added.
* Bad, because it increases maintenance burden and evaluation matrix size.
* Neutral, because it works best with strong tooling for dataset selection and reporting.

## More Information

### A good initial sample to start with

A reasonable starting dataset should include:

* A core sample of real transcripts across a small number of key meeting types.
* A balanced range of transcript lengths and speaker counts.
* Examples with:
  * Action items and owners
  * Dates/times and numeric details
  * Decisions and open questions
  * Contradictions, corrections, and backtracking
  * Multiple topics / agenda shifts

If references are not immediately available, the initial iteration can start with:

* LLM-generated reference summaries that are then spot-checked.
* A small, high-quality human-labeled subset used as calibration.

### Strategy for improving the dataset over time

We should improve the dataset continuously using:

* Failure-driven sampling: add examples where evaluation or production monitoring indicates regressions.
* Coverage-driven sampling: add examples to fill known gaps (meeting type, language patterns, domains).
* Periodic refresh: add a new slice of recent production-like data to prevent drift.

### Borderline / tricky cases

We should maintain a dedicated “tricky cases” subset used for regression testing, covering patterns such as:

* Negation and polarity ("did not", "won't")
* Numeric fidelity (amounts, counts, dates, times)
* Speaker attribution and ownership of action items
* Quoted speech vs commitments
* Contradictory statements and corrections ("actually")
* Subtle omissions (missing a key decision)

This subset can be built using:

* Human annotation of real failures.
* Synthetic generation with tight constraints and acceptance criteria.

### Dataset versioning and tracking impact on evaluation quality

We should version datasets explicitly (e.g., semantic versioning or date-based versions) and record:

* Dataset version identifier
* Composition (source breakdown: real/synthetic/hybrid)
* Labeling method (human vs LLM vs hybrid)
* Known caveats and change log

Evaluation runs should always log the dataset version. When the dataset changes, we should:

* Re-run evaluation on previous model/prompt versions to detect metric shifts.
* Track whether score changes are due to model changes or dataset changes.
* Maintain stable “frozen” regression subsets to preserve comparability over time.

Signoff or data agreement will be required for:

* Using any production or user data (privacy, retention, governance)
* Any data export outside approved storage systems
* Human labeling programs operating on sensitive data (process, QA, and compliance)
