***

# ADR-019: S3 Data Retention Policy for Audio and Transcripts

## Status

Proposed

Date of decision: 2026-02-18

## Context and Problem Statement

The "Minute" application processes "Official-Sensitive" audio recordings and generates transcripts. Currently, these files are stored in S3 indefinitely. To comply with UK GDPR "Data Minimisation" principles and the Department's security policies, we must implement an automated deletion policy. 

The challenge is balancing the security requirement to delete sensitive data as soon as possible against the operational requirement to retain data long enough to allow for retries in the event of a pipeline failure (e.g., LLM API downtime or Worker crashes). 

How long should we retain raw audio binaries and transcripts before automated permanent deletion?

## Considered Options

* **Option 1: 24-hour retention for raw audio; 30-day retention for transcripts.**
* **Option 2: 7-day retention for raw audio; 30-day retention for transcripts.**
* **Option 3: 30-day retention for all data.**

## Decision Outcome

**Option 2**, because it provides a sufficient "Retry Window" to handle system failures that occur over weekends or bank holidays, while significantly reducing the Department's data footprint compared to the current "indefinite" state.

## Pros and Cons of the Options

### Option 1: 24-hour retention for raw audio

This is the most aggressive stance for privacy and data minimisation.

* **Good**, because it minimizes the window of risk for the most sensitive data (audio binaries) to the absolute minimum.
* **Bad**, because it creates a high risk of permanent data loss. If a transcription job fails on a Friday afternoon, the raw audio would be deleted by Saturday afternoon, making it impossible for engineers to investigate and re-run the job on Monday.

### Option 2: 7-day retention for raw audio (Selected)

A middle-ground approach designed for operational resilience.

* **Good**, because it covers all "non-working day" scenarios, including long weekends and bank holidays, ensuring engineers have time to recover from pipeline failures without losing the source data.
* **Good**, because 7 days is still a significantly improved security posture over the current indefinite storage.
* **Neutral**, because it requires a slightly higher storage cost than Option 1 (though negligible for speech-to-text volumes).

### Option 3: 30-day retention for all data

A conservative approach often used as a default in MHCLG projects.

* **Good**, because it provides a massive buffer for any manual auditing or quality assurance checks.
* **Bad**, because holding sensitive audio binaries for 30 days when they are typically processed in minutes is difficult to justify under GDPR "storage limitation" clauses.

## More Information

The implementation will utilize **S3 Lifecycle Configurations** targeting specific prefixes (`app_data/user-uploads/` for audio and `app_data/transcripts/` for text) to ensure that the logic is applied granularly based on data type.

***
