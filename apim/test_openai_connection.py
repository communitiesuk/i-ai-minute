"""
Test script to mimic the OpenAI connection logic from common/llm/client.py and adapters.

This script simulates the connection process to verify bearer token authentication
is working correctly before running the full application.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def test_openai_connection():
    """Test the OpenAI connection with bearer token authentication."""
    
    # Get settings from environment (mimicking settings.py)
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    subscription_key = os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY")
    bearer_token = os.getenv("AZURE_OPENAI_BEARER_TOKEN")
    model = os.getenv("BEST_LLM_MODEL_NAME", "gpt-4")
    
    logger.info("Connection parameters:")
    logger.info(f"  Azure Endpoint: {azure_endpoint}")
    logger.info(f"  Azure Deployment: {azure_deployment}")
    logger.info(f"  API Version: {api_version}")
    logger.info(f"  API Key: {'SET' if api_key else 'NOT SET'}")
    logger.info(f"  Subscription Key: {'SET' if subscription_key else 'NOT SET'}")
    logger.info(f"  Bearer Token: {'SET' if bearer_token else 'NOT SET'}")
    logger.info(f"  Model: {model}")
    
    # Build custom headers (mimicking azure_openai.py)
    default_headers = {}
    if subscription_key:
        default_headers["Ocp-Apim-Subscription-Key"] = subscription_key
        logger.info("Using custom Ocp-Apim-Subscription-Key header for API Manager")
    if bearer_token:
        default_headers["Authorization"] = f"Bearer {bearer_token}"
        logger.info("Using Bearer token authentication for API Manager")
    
    # Use a dummy API key since we're using custom auth
    if default_headers:
        api_key = "dummy-key-not-used"
    
    # Create Azure OpenAI client
    # For custom API Gateway routing, we need to use base_url and construct the full path
    # to match the working apim_python_script.py approach
    base_url = f"{azure_endpoint}/deployments/{azure_deployment}"
    logger.info(f"Using base_url: {base_url}")
    logger.info(f"Using default_headers: {list(default_headers.keys())}")
    
    try:
        client = AsyncAzureOpenAI(
            base_url=base_url,
            api_key=api_key,
            api_version=api_version,
            default_headers=default_headers,
        )
        logger.info("✓ AsyncAzureOpenAI client created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create AsyncAzureOpenAI client: {e}")
        return
    
    # Try a simple chat completion (mimicking adapter.chat())
    test_messages = [
        {"role": "user", "content": "Say 'Hello, this is a test' and nothing else."}
    ]
    
    try:
        logger.info("Attempting to send chat completion request...")
        response = await client.chat.completions.create(
            model=azure_deployment,  # Use deployment name as model when using Azure
            messages=test_messages,
            temperature=0.0,
            max_tokens=100,
        )
        
        logger.info("✓ Request successful!")
        logger.info(f"Response: {response.choices[0].message.content}")
        logger.info(f"Model used: {response.model}")
        logger.info(f"Tokens used: {response.usage.total_tokens}")
        
    except Exception as e:
        logger.error(f"✗ Request failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        if hasattr(e, 'status_code'):
            logger.error(f"Status code: {e.status_code}")
        if hasattr(e, 'response'):
            logger.error(f"Response: {e.response}")
    
    finally:
        # Cleanup if needed
        pass


if __name__ == "__main__":
    asyncio.run(test_openai_connection())
