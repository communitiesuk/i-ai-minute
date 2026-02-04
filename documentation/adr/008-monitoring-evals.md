# ADR-008: Evals Monitoring

## Status

{Draft | Proposed | Accepted | Rejected | Superseded}

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

Current monitoring of AI system components relies primarily on user action logging, which is reactive and imperfect. User feedback only surfaces after significant issues occur, missing gradual quality deterioration and failing to pinpoint which system component is underperforming.

Without continuous evaluation monitoring, performance changes from upstream providers (e.g., Azure AI Speech, LLM API updates) can be misattributed to new features, leading to incorrect decisions. Third-party AI services frequently update to address user-reported issues and improve aggregate performance, which can inadvertently cause regressions on specific tasks important to our use case.

How can we implement ongoing evaluation monitoring to detect quality changes, distinguish between feature-related and provider-related performance shifts, and maintain visibility into system health?

## Considered Options

* Tiered dataset based evals with continuous monitoring
* Continuous monitoring with full dataset
* Evaluation on flagged inputs
* Third-party moderation/safety APIs
* Shadow evaluation
* Random sampling of live production data
* No additional monitoring

## Decision Outcome

{Title of Option X}, because {summary justification / rationale}.

## Pros and Cons of the Options

### Tiered dataset based evals

A stratified evaluation approach using multiple dataset subsets of varying sizes: a comprehensive dataset for pre-deployment validation, a medium subset for weekly continuous monitoring, and a minimal subset for rapid PR-level regression detection.

* Good, because it enables rapid feedback on prompt changes before full deployment.
* Good, because evaluation cost and coverage are tunable based on the tier selected.
* Good, because additional tiers can be introduced incrementally to provide granular insights.
* Good, because it balances thoroughness with operational efficiency.
* Good, because it allows for different levels of confidence in different scenarios.
* Good, because it makes updating the dataset easier, as it doesn't consider the dataset as an unchanging monolith. 
* Bad, because it requires medium-high implementation effort to design tier structure and maintain multiple dataset versions.
* Bad, because comparing results across different subset tiers requires additional normalization metrics.
* Bad, because partial evaluations create coverage gaps and potential blind spots.
* Bad, because maintaining multiple synchronized dataset versions adds operational overhead.
* Neutral, because evaluation quality scales proportionally with subset size.

### Continuous monitoring with full dataset

Run the complete evaluation dataset on a regular cadence (e.g., weekly or per release) to maintain comprehensive quality oversight without subset-based compromises.

* Good, because it provides complete coverage without blind spots or sampling bias.
* Good, because results are directly comparable across all evaluation runs. This benefit disapears once the dataset is updated.
* Good, because it eliminates the complexity of maintaining multiple dataset tiers.
* Good, because it ensures consistent quality baselines over time.
* Bad, because it requires medium implementation effort to set up scheduling and result tracking infrastructure.
* Bad, because inference costs accumulate rapidly with frequent full-dataset runs.
* Bad, because feedback cycles are slower, delaying detection of regressions.
* Bad, because it lacks granularity for rapid PR-level validation.
* Bad, because resource intensity may limit evaluation frequency.

### Evaluation on flagged inputs

Collate and evaluate inputs flagged as problematic through explicit user feedback (e.g., thumbs down ratings), implicit signals (e.g., immediate response dismissal), or other indicators (e.g., hallucination detection). Use automated evaluation methods such as LLM-as-a-judge to assess these inputs against existing criteria.

* Good, because it focuses resources on actual user pain points rather than re-evaluating all inputs.
* Good, because it identifies patterns in poor performance and enriches evaluation datasets with challenging real-world cases.
* Good, because it surfaces issues unknown to the team or not captured in pre-defined evaluation datasets.
* Good, because it creates a direct feedback loop between production issues and quality improvement.
* Bad, because it requires high implementation effort to build flagging infrastructure and integrate multiple signal sources.
* Bad, because evaluation results are not directly comparable across time periods or releases.
* Bad, because it misses issues that users don't flag or can't articulate.
* Bad, because it can create a biased view of performance based on incorrect usage patterns.
* Bad, because it creates massive blind spots that can mask overall system performance degradation.
* Neutral, because it requires additional infrastructure to collect, flag, and route problematic inputs.
* Neutral, because it is partially covered by logging user interactions with the system in PostHog.

### Third-party moderation/safety APIs

Use external services (e.g., OpenAI moderation, Lakera Guard) to evaluate specific risk categories such as harmful content, PII leakage, or policy violations using the live user data.

* Good, because it leverages 3rd party specialized expertise in safety and moderation domains.
* Good, because it is maintained and updated externally without internal resource investment.
* Good, because it can be used to enhance the evaluation dataset with additional safety criteria and examples.
* Bad, because it requires medium implementation effort to integrate APIs and handle responses.
* Bad, because it incurs ongoing operational costs that scale directly with usage.
* Bad, because it creates vendor dependency and potential lock-in.
* Bad, because customization options are limited to the provider's API capabilities.
* Bad, because it may introduce latency into the evaluation pipeline.
* Bad, because generic risk taxonomies may not align well with our domain-specific requirements.

### Shadow evaluation

Run old prompt/model variants alongside the new production version on live traffic (without showing results to users) to compare performance after full deployment, using LLM-as-a-judge evaluations. This approach can also be reversed as part of pre-production promotion checks by running the new version in shadow mode before promoting it to production (but that would not be considered a part of monitoring at that point).

* Good, because it uses real-world data that reflects actual user behavior and edge cases.
* Good, because it enables direct performance comparison between versions on identical inputs.
* Good, because it can validate improvements or catch regressions after (or before) full rollout.
* Bad, because it requires high implementation effort to build dual-execution infrastructure.
* Bad, because it doubles inference costs by running both versions simultaneously. 
* Bad, because it may require additional evaluation deferral logic to handle peak times without slowing down the overall system.
* Bad, because it requires traffic routing infrastructure and orchestration logic.
* Bad, because it may not catch issues that depend on user interaction with the output.
* Neutral, because the duration of shadow testing affects both cost and confidence in results.

### Random sampling of live production data

Periodically sample a random subset of production inputs and outputs, then run LLM-as-a-judge evaluations against existing criteria to monitor system performance on real-world data.

* Good, because it provides visibility into actual production behavior without user feedback dependency.
* Good, because sampling costs can be controlled by adjusting sample size and frequency.
* Bad, because it requires medium-high implementation effort to build sampling logic and evaluation pipelines.
* Bad, because evaluation results are not directly comparable across time periods due to varying input distributions.
* Bad, because extracting actionable insights is difficult without consistent baselines or controlled inputs.
* Bad, because mature evaluation datasets already cover common cases, making most sampled data redundant.
* Bad, because it lacks the signal-to-noise ratio of curated evaluation datasets.
* Bad, because it may raise privacy concerns when storing and evaluating real user interactions.
* Neutral, because effectiveness depends on how representative the random sample is of actual quality issues.

### No additional monitoring

Maintain the current approach of relying solely on user logging and feedback mechanisms (e.g., PostHog analytics) without implementing dedicated evaluation monitoring infrastructure.

* Good, because it incurs no additional resource costs.
* Good, because it avoids complexity of building and maintaining evaluation systems.
* Good, because it requires no additional engineering effort or team resources.
* Good, because it sidesteps privacy concerns associated with storing and evaluating user data.
* Bad, because it provides no proactive detection of gradual quality degradation.
* Bad, because it cannot distinguish between feature-related and provider-related performance changes.
* Bad, because it relies entirely on users encountering and reporting issues.
* Bad, because it offers no visibility into system performance between user-reported incidents.
* Bad, because it makes it difficult to validate whether changes improve or harm quality.
* Bad, because upstream provider updates may silently degrade performance on critical tasks.
* Neutral, because the risk level depends on system maturity and stability of upstream dependencies.

## More Information

{Optionally, any supporting links or additional evidence}