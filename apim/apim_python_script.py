"""
Utility script for invoking the AZC APIM hosted Azure OpenAI endpoint.

Prerequisites:
    - Azure CLI installed and logged-in
      (`az login --scope api://api.azc.test.communities.gov.uk/.default`)
    - `requests` library available (`pip install requests`)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict
from dotenv import load_dotenv
import requests

load_dotenv()

DEPLOYMENT_ID = os.getenv("DEPLOYMENT_ID")
API_VERSION = os.getenv("API_VERSION")
TOKEN_SCOPE = os.getenv("TOKEN_SCOPE")
BASE_URL = os.getenv("BASE_URL")
SUBSCRIPTION_KEY = os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY")



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
    return payload["accessToken"]


def invoke_chat_completion(
    access_token: str, messages: list[dict[str, str]]
) -> Dict[str, Any]:
    """Send a chat-completions request to the deployment."""
    url = f"{BASE_URL}/{DEPLOYMENT_ID}/chat/completions"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
    }
    params = {"api-version": API_VERSION}
    body = {"messages": messages, "max_tokens": 128, "temperature": 0}

    response = requests.post(url, params=params, headers=headers, json=body)
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
    response.raise_for_status()
    return response.json()


def main() -> None:
    token = get_access_token()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello to the APIM test team."},
    ]
    result = invoke_chat_completion(token, messages)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
