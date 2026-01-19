# ailg-evals

Config-driven LangChain eval runner for DialogSum-style conversational summarization.

## Quickstart

1) Create environment and install deps:

```bash
uv sync
```

2) Run eval:

```bash
uv run ailg-evals --config configs/default.yaml --split test --limit 50
```

Outputs are written to `runs/<run_id>/results.jsonl` and `runs/<run_id>/summary.json`.
