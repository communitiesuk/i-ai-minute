## Starting App

This is mostly covered in the README.md, but as a quick guide:

- [Install Docker](https://docs.docker.com/desktop/setup/install/mac-install/).
- Make a copy of the `.env.example` file and name it `.env`.
- Run `docker compose up --watch`. It'll take a few seconds to get up and running.

Once this is done, the frontend will be accessible on http://localhost:3000/. However, none of the core functionality will be available due to missing API keys.

## Other Notes

### Backend

- [Intsall Poetry](https://python-poetry.org/docs/).
- In the root directory, run `poetry install`.
  - If using VS Code, open the command palette (`Command+Shift+P`), click 'Python: Select Interpreter' and select the 'minute-xxxxxxxxxx' env file Poetry has just created.

### Frontend

- [Install node](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating).
- In the `/frontend` directory, run `npm install`.
