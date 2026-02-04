# ADR-009: Prompt Optimization Data Collection

## Status

{Draft | Proposed | Accepted | Rejected | Superseded}

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

Prompt optimization is essential for maintaining and improving AI system performance, but it requires high-quality training data that reflects real-world usage patterns and failure modes. Without systematic data collection, prompt improvements rely on anecdotal evidence and ad-hoc issue reports, making optimization reactive and inconsistent.

Current approaches to collecting optimization data face significant challenges. Manual annotation requires substantial human resources, introduces inconsistency, and struggles to scale with production volume. Passive collection methods may miss critical context about why failures occur. Active feedback solicitation risks user fatigue and selection bias. Automated detection systems can only flag issues that have been anticipated and defined.

The challenge is compounded by the need to balance data quality, collection costs, user experience impact, and the risk of biasing the system toward specific user segments or predefined problem categories.

How should we collect data to support prompt optimization while balancing resource constraints and data quality requirements?

## Considered Options

* Automated collection via user-flagged inputs
* Prompted user feedback collection
* Automated collection via system-flagged inputs
* Manual annotation of production samples
* No systematic data collection

## Decision Outcome

{Title of Option X}, because {summary justification / rationale}.

## Pros and Cons of the Options

### Automated collection via user-flagged inputs

Leverage monitoring infrastructure to automatically collect problematic inputs flagged through explicit user feedback (thumbs down, corrections) and implicit signals (immediate dismissal, repeated queries).

* Good, because user corrections provide direct examples of desired outputs for optimization.
* Good, because it captures issues that users actually care about and experience.
* Good, because it creates a continuous feedback loop between production issues and system improvements.
* Good, because it scales automatically with system usage without additional human resources.
* Bad, because it requires high implementation effort to build collection and routing infrastructure.
* Bad, because data quality depends on user engagement with feedback mechanisms.
* Bad, because it may miss edge cases that users don't flag or can't articulate.
* Bad, because it relies on users recognizing and reporting issues.
* Neutral, because it builds on monitoring infrastructure described in ADR-008: Evals Monitoring.

### Prompted user feedback collection

Actively prompt users to provide feedback through structured questions after specific interactions, collecting more detailed and verbose responses than passive flagging. Users can be asked follow-up questions to clarify issues, suggest improvements, or rate specific aspects. Responses can be processed by LLMs to extract actionable insights and patterns (such as axial coding).

* Good, because it yields richer, more detailed feedback than binary flags or simple corrections.
* Good, because structured prompts can guide users to provide specific types of feedback needed for optimization.
* Good, because LLM processing can extract patterns and insights from verbose user responses at scale.
* Good, because it can capture nuanced user preferences and expectations that implicit signals miss.
* Good, because it provides more context around why something failed, not just that it failed.
* Bad, because it requires high implementation effort to design prompt flows and LLM processing pipelines.
* Bad, because it adds friction to the user experience and may reduce engagement if overused.
* Bad, because response rates may be low if users perceive surveys as burdensome.
* Bad, because LLM processing of feedback adds inference costs and potential interpretation errors.
* Bad, because it requires careful UX design to balance feedback collection with user experience, including considerations for bundling prompts.
* Bad, because it can give disproportionate influence to highly engaged users, potentially steering the system in directions that don't benefit the broader user base.
* Neutral, because prompt timing and frequency significantly impact both data quality and user satisfaction.

### Automated collection via system-flagged inputs

Use automated detection systems to identify problematic outputs without requiring user intervention. This includes hallucination detection checks, third-party safety APIs (e.g., OpenAI moderation, Lakera Guard), and other automated quality checks that may be introduced later.

* Good, because it catches issues proactively without waiting for user reports.
* Good, because it provides consistent, objective flagging criteria across all outputs.
* Good, because it can detect subtle issues that users might not notice or report.
* Good, because it scales automatically and doesn't depend on user engagement.
* Good, because additional checks can be added incrementally as new quality criteria emerge.
* Bad, because it requires medium-high implementation effort to integrate multiple detection systems.
* Bad, because automated checks may produce false positives that dilute dataset quality.
* Bad, because it incurs ongoing operational costs for third-party API usage.
* Bad, because system-flagged data lacks user corrections showing desired outputs.
* Bad, because it can only detect issues within predefined categories and criteria, missing unexpected failure modes that weren't anticipated.
* Neutral, because it complements user-flagged collection by catching different types of issues.

### Manual annotation of production samples

Periodically sample production inputs and have human annotators label them with quality scores, corrections, or categorizations to build training datasets for prompt optimization.

* Good, because it provides high-quality, consistent annotations when done by trained annotators.
* Good, because it allows for nuanced judgments that automated systems might miss.
* Bad, because it requires high ongoing resource investment in annotation labor.
* Bad, because it introduces significant delays between data collection and optimization cycles.
* Bad, because annotation consistency is difficult to maintain across multiple annotators.
* Bad, because it doesn't scale with production volume without proportional resource increases.
* Bad, because annotator availability creates bottlenecks in the optimization pipeline.
* Bad, because annotator selection and biases can reinforce existing system biases rather than correcting them.

### No systematic data collection

Rely on ad-hoc issue reports and informal feedback without structured data collection for prompt optimization.

* Good, because it requires no implementation effort or ongoing operational costs.
* Good, because it avoids privacy and data handling complexities.
* Bad, because it misses opportunities for systematic quality improvement.
* Bad, because prompt optimization becomes reactive and inconsistent.
* Bad, because it prevents automated prompt engineering and continuous improvement workflows.
* Bad, because performance issues may persist undetected without structured feedback.

## Links

* Related to ADR-008: Evals Monitoring (data collection infrastructure)