## Starting App

This is mostly covered in the `README.md`, but as a quick guide:

- [Install Docker](https://docs.docker.com/desktop/setup/install/mac-install/).
- Make a copy of the `.env.example` file and name it `.env`.
- Run `docker compose up --watch`. It'll take a few seconds to get up and running.

Once this is done, the frontend will be accessible on http://localhost:3000/. However, features requiring transcription and LLM services will be unavailable due to missing API keys.

To get this functionality, you'll only need to fill in keys related to a transcription service and an LLM service, and then configure `common/settings.py` accordingly. For example, for Azure (synchronous) transcription and LLM services, you'd need to fill in the following:

In `.env`:

- Transcription: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
- LLM: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_DEPLOYMENT`, `AZURE_API_VERSION`

In `common/settings.py`:

- Update `FAST_LLM_PROVIDER`, `FAST_LLM_MODEL_NAME`, `BEST_LLM_PROVIDER`, and `BEST_LLM_MODEL_NAME` correspondingly.

This should be sufficient for local development. Keys related to 'AWS', 'Google cloud', and 'other' (Sentry/Posthog) are not required. After updating `.env`, restart the Docker container to apply changes

Note: Our transcription and LLM API keys are managed via Azure APIM. The APIM LLM key requires a new LLM adapter to integrate with the existing code.

## Local Development

### Backend Environment

- [Install Poetry](https://python-poetry.org/docs/).
- In the root directory, run `poetry install`.
  - If using VS Code, open the command palette (`Command+Shift+P`), click 'Python: Select Interpreter' and select the 'minute-xxxxxxxxxx' env file Poetry has just created.

### Frontend Environment

- [Install node](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating).
- In the `/frontend` directory, run `npm install`.
