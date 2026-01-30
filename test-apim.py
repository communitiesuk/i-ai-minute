from __future__ import annotations
 
import json
import os
import shutil
import subprocess
import sys
from typing import Any, cast
from openai.types.chat import ChatCompletionMessageParam

 
from openai import OpenAI
 
 
DEPLOYMENT_ID = "minute-gpt4o"
API_VERSION = "2024-10-21"
TOKEN_SCOPE = "api://api.azc.test.communities.gov.uk/.default"
SUBSCRIPTION_KEY = "35ddfd28ad164ab79927019bea8fd901"
BASE_URL = (
    "https://api.azc.test.communities.gov.uk/"
    "minute/openai001"
)
 
 
def get_access_token() -> str:
    """Fetch an AAD token using an env override or Azure CLI."""
    env_token = (
        os.getenv("APIM_ACCESS_TOKEN")
        or os.getenv("APIM_BEARER_TOKEN")
        or os.getenv("AZ_ACCESS_TOKEN")
    )
    if env_token:
        return env_token.strip()
 
    if shutil.which("az") is None:
        raise RuntimeError(
            "Azure CLI is not available and no access token override was provided. "
            "Install Azure CLI or export APIM_ACCESS_TOKEN with a valid bearer token."
        )
 
    command = [
        "az",
        "account",
        "get-access-token",
        "--scope",
        TOKEN_SCOPE,
        "--output",
        "json",
    ]
 
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print("Failed to fetch access token via Azure CLI.", file=sys.stderr)
        print(exc.stderr.strip(), file=sys.stderr)
        print(
            "Run `az login --scope "
            f"{TOKEN_SCOPE}` or export APIM_ACCESS_TOKEN before executing this script.",
            file=sys.stderr,
        )
        raise
 
    payload = json.loads(result.stdout)
    return cast(str, payload["accessToken"])
 
 
def build_client(access_token: str) -> OpenAI:
    """Create an OpenAI client configured for APIM + Azure OpenAI."""
    return OpenAI(
        base_url=f"{BASE_URL}/deployments/{DEPLOYMENT_ID}",
        # Use the bearer token for Authorization and send the APIM subscription key
        # explicitly so APIM's subscription check succeeds.
        api_key=access_token,
        default_headers={
            "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
        },
    )
 
 
def invoke_chat_completion(client: OpenAI, messages: list[dict[str, str]]) -> Any:
    """Send a chat-completions request to the deployment."""
    return client.chat.completions.create(
        model=DEPLOYMENT_ID,
        messages=cast(list[ChatCompletionMessageParam], messages),
        max_tokens=128,
        temperature=0,
        extra_query={"api-version": API_VERSION},
    )
 
 
def main() -> None:
    token = get_access_token()
    client = build_client(token)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello to the APIM test team."},
    ]
    result = invoke_chat_completion(client, messages)
    print(result)
 
 
if __name__ == "__main__":
    main()