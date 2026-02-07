import logging
import sys
import asyncio
from common.llm.adapters.ollama import OllamaModelAdapter
from common.types import GuardrailScore

# Setup logging to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

async def test_ollama_json():
    adapter = OllamaModelAdapter(model="llama3.2", base_url="http://ollama:11434/v1")
    
    # Mocking the schema of GuardrailScore
    # GuardrailScore: score (float), reasoning (str)
    
    messages = [
        {"role": "system", "content": "You are a QA bot."},
        {"role": "user", "content": "Evaluate this text: 'The meeting was good.' expected: 'The meeting was bad.'"}
    ]
    
    try:
        print("Sending request to Ollama...")
        result = await adapter.structured_chat(messages, GuardrailScore)
        print("Success! Result:", result)
    except Exception as e:
        print("Failed:", e)

if __name__ == "__main__":
    asyncio.run(test_ollama_json())
