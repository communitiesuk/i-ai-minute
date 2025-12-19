## APIM Test Utility (Postman Flow)

This guide explains how to call the `testteammhclg-gpt4o` Azure OpenAI deployment exposed via AZC APIM using **Postman**. Unlike the Python helper script, Postman cannot obtain an Azure AD token automatically, so you must paste a manually generated bearer token for every session.

### 1. Prerequisites

- Postman desktop app (recommended) or the Postman CLI with a compatible GUI environment.
- An active Azure AD bearer token for the scope `api://api.azc.test.communities.gov.uk/.default`.
- The APIM subscription key for the deployment (same value you would place in `SUBSCRIPTION_KEY` in `apim_python_script.py`).

### 2. Manually generate an AAD bearer token

You can use any mechanism your organization supports. Common options:

1. Azure CLI (device-code) – run:
   ```bash
   az account get-access-token \
     --scope api://api.azc.test.communities.gov.uk/.default \
     --output tsv \
     --query accessToken
   ```
   Copy the resulting token.
2. An internal portal that issues tokens for APIM testing – copy the full `eyJ...` JWT string.

💡 The token typically expires within 60 minutes, so plan to refresh it when Postman begins returning `401 Unauthorized`.

### 3. Create a Postman collection/environment

1. In Postman, create a new **Environment** (e.g., “APIM Test”).
2. Add the following variables (initial + current values):
   - `baseUrl` = `https://api.azc.test.communities.gov.uk/testteammhclg/openai001`
   - `deploymentId` = `testteammhclg-gpt4o`
   - `apiVersion` = `2024-10-21`
   - `subscriptionKey` = `<your APIM subscription key>`
   - `accessToken` = `<paste bearer token>`
3. Save the environment and select it in the upper-right environment picker.

### 4. Configure the POST request

1. Create a new request named “Chat Completion”.
2. Method: `POST`
3. URL:
   ```
   {{baseUrl}}/deployments/{{deploymentId}}/chat/completions?api-version={{apiVersion}}
   ```
4. **Headers**:
   - `Authorization`: `Bearer {{accessToken}}`
   - `Content-Type`: `application/json`
   - `api-key`: `{{subscriptionKey}}`
5. **Body** (raw JSON):
   ```json
   {
     "messages": [
       { "role": "system", "content": "You are a helpful assistant." },
       { "role": "user", "content": "Say hello to the APIM test team via Postman." }
     ],
     "max_tokens": 128,
     "temperature": 0
   }
   ```
6. Send the request.

### 5. Handling token expiry

When the bearer token expires, APIM returns `401` with `{"error": {"code": "401", "message": "Access token is invalid or expired"}}`. Refresh the token (step 2) and update the `accessToken` environment variable in Postman before retrying.

With these steps, you reproduce the Python script’s behavior entirely within Postman while manually managing authentication.
