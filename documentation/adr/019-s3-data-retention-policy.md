***

# ADR-019: S3 Data Retention Policy for Audio and Transcripts

## Status

Proposed

**Date of decision:** 2026-02-18

## Context and Problem Statement

The "Minute" application processes "Official-Sensitive" audio recordings to generate transcripts and summaries. Currently, these files are stored in S3 indefinitely.

To comply with the **UK GDPR "Storage Limitation" principle (Article 5(1)(e))** and Departmental security policies regarding Official-Sensitive data, we must implement an automated deletion policy. We cannot justify holding raw audio binaries indefinitely when the primary value is extracted (transcribed) within minutes.

The challenge is balancing the security requirement to minimize the data footprint against the operational requirement to allow for service recovery. If the transcription pipeline fails (e.g., Worker crash, LLM API downtime), engineers need the source audio to retry the job.

Analysis of the codebase confirms that transcript text is stored exclusively within Aurora PostgreSQL JSONB columns. The S3 bucket serves only as a temporary landing zone for raw audio binaries.

How long should we retain raw audio binaries versus generated transcripts before automated permanent deletion?

## Considered Options

*   **Option 1: 24-hour retention for audio; 30-day retention for transcripts.**
*   **Option 2: 7-day retention for audio; 30-day retention for transcripts.**
*   **Option 3: 30-day retention for all data.**

## Decision Outcome

**Option 2**, because it provides a sufficient "Retry Window" to handle system failures that occur over weekends or bank holidays, while still significantly reducing the Department's liability compared to the current "indefinite" state.

We adopt a **Tiered Retention Strategy**:
1.  **Binaries (S3):** Expire after 7 days via S3 Lifecycle Rules. This minimizes the risk of voice-data leaks while allowing a window for pipeline retries.
2.  **Records (Aurora):** Retained according to Departmental Policy (e.g., 30 days), handled via a separate database cleanup process.

## Pros and Cons of the Options

### Option 1: 24-hour retention for raw audio
This is the most aggressive stance for privacy and data minimisation.

*   **Good:** Minimizes the window of risk for the most sensitive data (audio binaries) to the absolute minimum.
*   **Bad:** Creates a high risk of unrecoverable failure. If a transcription job fails on a Friday afternoon, the raw audio would be deleted by Saturday, making it impossible for engineers to investigate or re-drive the job on Monday.

### Option 2: 7-day retention for raw audio (Selected)
A middle-ground approach designed for operational resilience.

*   **Good:** Covers all "non-working day" scenarios (including Bank Holidays), ensuring engineers have time to recover from pipeline failures without losing the source data.
*   **Good:** Reduces storage costs and liability significantly compared to the current indefinite state.
*   **Bad:** Retains sensitive audio binaries for 6 days longer than strictly required for a "happy path" transaction.

### Option 3: 30-day retention for all data
A conservative approach often used as a default in legacy projects.

*   **Good:** Provides a massive buffer for manual auditing or quality assurance checks.
*   **Bad:** Hard to justify under GDPR "Data Minimisation." Keeping raw audio for 30 days when processing takes minutes creates an unnecessary accumulation of sensitive data.

## More Information

### Implementation
The policy will utilize **S3 Lifecycle Configurations** targeting specific prefixes:
*   `app_data/user-uploads/`: **Expire after 7 days.**
*   `app_data/transcripts/`: **Expire after 30 days.**

### Application Behavior
The application logic must handle cases where a user attempts to access a file that has been lifecycle-deleted. The frontend will display a "File Expired" status for historical records where the metadata exists in Postgres but the S3 object has been purged.