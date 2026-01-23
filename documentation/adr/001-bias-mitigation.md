# ADR-001: Mitigation of Bias in Minute System

## Status

Accepted

Date of decision: 2026-01-15

## Context and Problem Statement

Current Minute system has not been yet evaluated against bias, therefore we may be finding out soon that there is a significant amount of bias being introduced into the system. Therefore it is good to prepare mitigation strategies so that we can quickly mitigate the impact of bias or at least reduce the impact of bias on the overall system.

## Considered Options

* Anonymizing protected characteristics
* Warning frontline users about potential bias impacts
* Standardizing utterances through AI rephrasing
* Evaluating alternative LLM providers

## Decision Outcome

Evaluating alternative LLM providers, because we currently think it's the most plausible option to develop. It is lightweight compared to other options which require further research.

Note: Warning frontline users about potential bias impacts is "do nothing" equivalent for this decision. We will need to implement an apporpriate message for the user, but it is not a mitigation strategy for the system.

## Pros and Cons of the Options

### Anonymizing protected characteristics

This approach involves identifying and replacing protected characteristics (names, ages, gender, ethnicity) in transcripts with anonymized placeholders before processing through the summarization pipeline. This prevents the LLM from accessing demographic information that could influence summary generation.

* Good, because it directly removes the source of potential bias from protected characteristics.
* Good, because it can be implemented as a preprocessing step without modifying the core summarization pipeline.
* Good, because it provides a clear audit trail of what information was anonymized.
* Bad, because it may reduce summary quality if demographic context is relevant to the meeting content.
* Bad, because it requires robust NER pipelines to accurately identify all protected characteristics.
* Bad, because it doesn't address bias from linguistic variations or implicit demographic signals.
* Neutral, because effectiveness depends on the completeness of the anonymization process.

### Warning frontline users about potential bias impacts

This approach involves adding user interface warnings to alert frontline users when the system may produce biased outputs for specific demographics, based on bias testing results. Users would be informed about potential limitations before relying on summaries.

* Good, because it provides transparency about system limitations.
* Good, because it requires minimal technical implementation effort.
* Good, because it empowers users to make informed decisions about summary usage.
* Bad, because it doesn't actually mitigate the bias, only warns about it.
* Bad, because it may reduce user trust and adoption of the system.
* Bad, because warnings may be ignored or become normalized over time.
* Neutral, because it shifts responsibility to users rather than addressing the root cause.

### Standardizing utterances through AI rephrasing

This approach adds a preprocessing step where an AI model rephrases all meeting utterances into standardized English, removing linguistic variations that may correlate with protected characteristics (e.g., accent-influenced phrasing, dialectal variations). Importantly, this standardization step is done in a separate AI conversation. Therefore, the final summary pipeline will not be aware that the outputs were ever in a non-standardized form. The standardized transcript is then processed through the summarization pipeline. The user can still be shown the real transcript while benefiting from the bias-reducing effects of standardization.

* Good, because it could reduce bias from linguistic variations across demographic groups.
* Good, because it creates more uniform input for the summarization model.
* Bad, because it adds significant computational cost and latency to the pipeline.
* Bad, because it may lose important contextual nuances and speaker intent.
* Bad, because the standardization model itself may introduce new biases, though the reduced scope of the standardization step could potentially limit this compared to end-to-end bias, but will not eliminate bias on its own.
* Bad, because it requires additional LLM API calls, increasing operational costs.
* Bad, because it may become more complicated as the chunking strategy evolves, since standardization would benefit from chunks being comprehensive singular statements.
* Neutral, because effectiveness depends on the quality of the standardization model.
* Neutral, because it may identify bias we cannot address within closed-source model constraints.

### Evaluating alternative LLM providers

This approach involves comprehensively evaluating different LLM and transcription service providers using the bias testing framework to identify providers that perform best across demographic groups. The system would switch to the least biased provider option.

* Good, because it could identify providers with inherently lower bias.
* Good, because it may improve overall system performance beyond just bias metrics.
* Bad, because migration to new providers requires significant integration effort.
* Bad, because it may lead to selecting a provider that performs better on specific test cases but worse in general real-world scenarios.
* Neutral, because it may not produce conclusive results as different aspects of bias might be impacted in different ways.
* Neutral, because all closed-source models may have similar bias limitations.
* Neutral, because it requires ongoing evaluation as providers update their models.

## More Information

* Evaluating alternative LLM providers would require approval to use a large variety of LLM providers for comprehensive evaluation