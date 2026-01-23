# ADR-007: Voice-to-Text Transcription Evaluation for Minute

## Status

Accepted

Date of decision: 2026-01-16

## Context and Problem Statement

Minute ingests audio recordings (potentially up to ~1 hour) and produces a transcript via a pipeline that:

* Preprocesses the audio into the required format.
* Sends audio to a third-party transcription service.
* Receives text plus metadata such as speaker identification/diarization.

We need an evaluation approach for transcription quality from audio to text that is:

* Representative of real usage (long recordings, multiple speakers, interruptions).
* Able to measure both text accuracy and speaker identification quality.
* Actionable: able to pinpoint whether errors come from audio preprocessing, the vendor model, or diarization.

## Considered Options

* Ground-truth evaluation with human transcripts (preferred when available)
* Reference-free comparative evaluation across multiple transcription models
* Speaker diarization evaluation (separate or integrated)
* End-to-end evaluation (transcription → summary quality) vs component evaluation (audio → transcript)

## Decision Outcome

Ground-truth evaluation with human transcripts, with strong preference towards audio files of our target interactions, because it is the only approach that allows error rate analysis and consistent metric tracking.

We do not have a clear strategy for procuring this data yet. Initially, we are planning to use suitable open-source datasets as a starting point.

## Pros and Cons of the Options

### Ground-truth evaluation with human transcripts (preferred when available)

This approach uses a dataset of (audio file, human transcript) pairs. We run the pipeline (including preprocessing and third-party transcription), then compare the produced transcript against the human transcript.

Text accuracy can be measured using:

* Word error rate (WER) / character error rate (CER)
* Normalized edit distance
* Embedding similarity as a supplementary signal

If speaker labels exist in the human transcript, diarization can be evaluated using:

* Speaker-attributed WER (SA-WER) or similar speaker-aware accuracy measures
* Confusion of speaker assignment (how often words are attributed to the wrong speaker)

* Good, because good transcription examples of (file + human transcription) make evaluation close to “trivial” and objective.
* Good, because it enables clear pass/fail thresholds and regression detection.
* Good, because it supports vendor comparisons using a single trusted reference.
* Bad, because it is expensive and slow to create human transcripts at scale.
* Bad, because it requires consistent transcription guidelines (punctuation, numbers, hesitations) to avoid metric noise.
* Neutral, because the best metric may differ for product needs (verbatim vs clean transcript).

### Reference-free comparative evaluation across multiple transcription models

This approach is used when we have audio and transcripts from one model, but no human transcript. We run multiple transcription services/models and compare outputs.

Possible signals:

* Agreement rate between systems (pairwise similarity, consensus decoding)
* Outlier detection: flag segments where one model strongly disagrees with the others
* Heuristic checks: timestamps, missing segments, abnormal speaker counts

* Good, because it can be run on large volumes without human labeling.
* Good, because it can highlight unstable regions and identify likely failures.
* Bad, because without ground truth we cannot determine which model is “better” purely from disagreement.
* Bad, because high agreement can still be wrong (shared failure modes).
* Neutral, because it is best used as a triage signal to select clips for human transcription.

### Speaker identification / diarization evaluation

The third-party service provides speaker identification/diarization. We should treat speaker quality as a first-class evaluation dimension because it affects downstream summarisation (attribution, action items, decisions).

We can evaluate diarization in two ways:

* With ground truth: compare predicted speaker segments/labels to human-labeled diarization.
* Without ground truth: apply plausibility checks and consistency tests (speaker count stability, turn-taking patterns, label churn, long monologues split incorrectly).

* Good, because diarization errors can materially degrade summary quality even if the words are accurate.
* Good, because it isolates a key failure mode beyond raw text accuracy.
* Bad, because diarization ground truth is costly to create.
* Neutral, because some diarization errors may be acceptable depending on summarisation requirements.

### End-to-end evaluation vs component evaluation

We have a choice between:

* End-to-end evaluation (audio → transcript → summary quality)
* Component evaluation (audio → transcript quality only)

End-to-end evaluation:

* Good, because it reflects user-visible outcomes for the whole system.
* Bad, because it is harder to attribute failures to preprocessing vs transcription vs diarization vs summarisation.

Component evaluation:

* Good, because it isolates the transcription stage and makes the source of errors easier to identify.
* Bad, because it is not always straightforward to map a transcription metric change to a summary-quality change.

We can use both: component metrics for debugging and end-to-end metrics for product outcomes.

## More Information

### Dataset composition: clear vs bad examples

The dataset should include both:

* Clear examples: clean audio, minimal overlap, stable speakers.
* Bad examples: intentionally covering major failure modes.

Bad example categories to cover:

* Overlapping speech / interruptions
* Background noise (construction, cars, wind)
* Cross-talk / far-field microphones
* Accents / multilingual code-switching
* Named entities (people/orgs), technical terms, uncommon vocabulary
* Numbers/dates/amounts (high impact for action items)
* Long recordings with topic shifts

### Logging and versioning

Every transcription run should log:

* Audio preprocessing version/config (codec, sample rate, chunking)
* Transcription vendor/model identifier and settings
* Output schema version (timestamps, speaker labels)
* Dataset version for evaluation runs

This enables tracking regressions and distinguishing:

* Vendor/model changes
* Pipeline preprocessing changes
* Dataset changes

Signoff is required for:

* Use of real user audio (privacy, retention, consent)
* Sending audio to third-party vendors (security and compliance review)
* Human transcription/labeling programs

Qs raised:
* How much should we consider quality improvements of transcript after it's generated (LLMs fixing homophones, spelling errors, etc.)