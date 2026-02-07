# ailg-evals

Config-driven LangChain eval runner for DialogSum-style conversational summarization.

## Quickstart

1. Create environment and install deps:

```bash
uv sync
```

1. Run eval:

```bash
uv run ailg-evals --config configs/default.yaml --split test --limit 50
```

Outputs are written to `runs/<run_id>/results.jsonl` and `runs/<run_id>/summary.json`.

## Running a new experiment (This process will likely be updated in the future)

At a high level, an experiment is defined by:

- A config file in `configs/` (dataset, model/judge settings, and which prompt templates to use).
- Prompt templates in `prompts/` (how we ask the model to summarise, and how we ask the judge to score).

Update the config file and/or prompt templates as needed, then run the experiment.
