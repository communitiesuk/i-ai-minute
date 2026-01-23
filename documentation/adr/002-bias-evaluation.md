# ADR-002: Identifying the impact of bias in the Minute system in the post-transcription generation steps

## Status

Accepted

Date of decision: 2026-01-15

## Context and Problem Statement

The Minute system has not been evaluated for potential bias, which poses a risk that summaries may be influenced by protected characteristics. This could result in outputs with varying sentiment or tone based on demographic attributes, disproportionately impacting specific groups. We need to assess whether changes to protected characteristics or related parameters affect the sentiment and content of generated summaries.

## Considered Options

* Sensitive data substitution testing
* Synthetic data testing with linguistic variation

## Decision Outcome

Sensitive data substitution testing, because it is a minimal viable approach which doesn't have a clear downside due to muddling of the content.

## Pros and Cons of the Options

### Sensitive data substitution testing

This approach uses named entity recognition to identify protected characteristics (names, ages, gender) in transcripts, then creates alternate versions with substituted values from different demographic groups. By comparing outputs across these variations, we can measure how the system's summaries are influenced by the embeddings of protected characteristic tokens. Bias is measured using sentiment analysis pipelines to compare sentiment scores between reference and substituted texts. Additionally, an LLM-as-judge system evaluates whether specific statements are handled consistently across protected characteristic variations, assessing factors such as statement inclusion and comprehensiveness.

* Good, because it directly tests system reactions to specific protected characteristics.
* Good, because it provides quick feedback on anonymization value.
* Good, because it produces quantifiable insights into bias from protected characteristics.
* Good, because it creates a testing dataset that can be validated without specific linguistic expertise.
* Bad, because it requires non-trivial NER pipelines and LLMs to generate synthetic meeting transcripts.
* Neutral, because it requires significant effort to define LLM-as-judge evaluation criteria for comprehensiveness and statement handling analysis. Robust LLM-as-judge criteria may require a small amount of human annotation.

### Synthetic data testing with linguistic variation

This approach generates synthetic transcript data that exemplifies linguistic differences across demographic groups where the differentiating factor may be a protected characteristic. This testing reveals how the system biases outputs based on these inputs. When combined with sensitive data substitution testing, protected characteristics should be replaced with anonymized tags, allowing this step to isolate the linguistic implications of bias and provide clearer insights. Bias is measured using sentiment analysis to compare sentiment scores across linguistic variations, and an LLM-as-judge system to evaluate consistency in statement handling, inclusion, and comprehensiveness.

* Good, because it reveals comprehensive bias insights and could provide proof of system resilience.
* Good, because when combined with substitution testing, it identifies whether bias stems from explicit protected characteristics or implied linguistic differences.
* Bad, because it assumes LLMs can accurately represent speech of minority groups, which is questionable given limited training data for these demographics.
* Bad, because the testing dataset would require linguistic experts to validate whether the synthetic linguistic representation of specific demographics is accurate.
* Bad, because LLM-generated synthetic data may include overly stereotypical or offensive statements, particularly as some dialects are primarily spoken rather than written, reducing LLMs' ability to accurately represent them; only linguists with expertise on the specific dialect would be a solid source of truth for validation.
* Bad, because certain linguistic qualities of a statement may intentionally portray negativity (such as expressions of dishonesty), and the system might overfit to correct these negatives, introducing an opposite bias; only linguists with dialect expertise can reliably distinguish intentional negative expression from bias.
* Neutral, because it may identify aspects of bias that are impossible to address within our constraints of using closed-source cloud models.
* Neutral, because it requires significant effort to define LLM-as-judge evaluation criteria for comprehensiveness and statement handling analysis. Robust LLM-as-judge criteria may require a small amount of human annotation.

---

## More Information

Signoff is required for:
* External anonymization techniques
* LLM services for synthetic data generation
* (Potentially) Cloud-based advanced NLP tools to enhance named entity recognition pipelines