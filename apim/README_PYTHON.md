## APIM Test Utility

`apim_python_script.py` is a small helper script for invoking the AZC APIM-hosted Azure OpenAI deployment `testteammhclg-gpt4o`. It fetches an Azure AD bearer token (either via Azure CLI or from an environment variable) and then issues a chat completion request against APIM.

### Prerequisites

- macOS or Linux shell with Python 3.9+ available as `/usr/bin/python3`.
- [`requests`](https://pypi.org/project/requests/) installed for the selected Python interpreter.
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) installed **and logged in** to the tenant that exposes the APIM instance, unless you provide a bearer token manually.
- An APIM subscription key with access to the deployment (set this as `SUBSCRIPTION_KEY` in the script).

### Authentication

The script tries authentication in this order:

1. Use a bearer token supplied via one of these environment variables (first non-empty wins):
   - `APIM_ACCESS_TOKEN`
   - `APIM_BEARER_TOKEN`
   - `AZ_ACCESS_TOKEN`
2. Fall back to `az account get-access-token --scope api://api.azc.test.communities.gov.uk/.default`.

Therefore you can either:

- **Login via Azure CLI**
  ```bash
  az login --scope api://api.azc.test.communities.gov.uk/.default \
           --allow-no-subscriptions
  # Verify
  az account show
  ```
  If you see the tenant-selection prompt, choose the tenant-level context (e.g., option `1`) so that `az account get-access-token` works even without assigned subscriptions.
- **Provide a token manually**
  ```bash
  export APIM_ACCESS_TOKEN="<paste AAD bearer token>"
  ```

If Azure CLI reports `Please run 'az login' to setup account` or `No subscriptions found`, your current account is not logged into the correct tenant. Either login with an account that has access or use the manual token method.

### Running the script

```bash
cd /Users/abdikadirhassan/Projects/apim_test
/usr/bin/python3 apim_python_script.py
```

The script will:

1. Fetch an access token using the logic above.
2. Send a chat-completion request to `https://api.azc.test.communities.gov.uk/testteammhclg/openai001/deployments/testteammhclg-gpt4o/chat/completions?api-version=2024-10-21`.
3. Print the JSON response to stdout.

### Troubleshooting

- **`NotOpenSSLWarning`** – macOS system Python is linked against LibreSSL. The warning is harmless; requests will still work over HTTPS.
- **`Please run 'az login'`** – Run `az login` (optionally with `--scope` or `--tenant`) so the CLI can mint tokens, or export `APIM_ACCESS_TOKEN`.
- **Connection timeouts** – Usually transient or caused by VPN/firewall rules; retry after confirming you’re on the expected corporate network.

### Customizing the request

Edit the constants near the top of `apim_python_script.py`:

- `DEPLOYMENT_ID` – target model deployment.
- `API_VERSION` – API version query parameter.
- `BASE_URL` – APIM host and resource path.
- `SUBSCRIPTION_KEY` – APIM subscription key header (replace the placeholder value with your real key).

Adjust `messages`, `max_tokens`, or `temperature` in `main()` as needed.
