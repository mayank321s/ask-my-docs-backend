import os
import requests
from typing import List, Dict

# URL of the locally running Ollama server (default port 11434)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def askOllamaLlm(question: str, context_chunks: List[Dict], model: str = "llama3.1") -> str:
    """Send the question plus context to an Ollama-hosted model (default: Llama-3 7B).
Pass a different `model` arg to override."""

    # Build a single prompt that contains all context chunks
    context = "\n\n".join(
        chunk["fields"].get("chunk_text", "") for chunk in context_chunks
    )

    prompt = (
        "Use the following context to answer the question as accurately as possible.\n\n"
        f"{context}\n\nQuestion: {question}"
    )   
    payload = {
        "model": model, 
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        # Ollama returns the answer in the "response" field
        return data.get("response", "")
    except requests.RequestException as exc:
        # Surface network or API issues up the stack
        raise RuntimeError(f"Failed to query Ollama: {exc}") from exc
    
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_MODEL_URL = "https://1lmhubpoc8598770946.services.ai.azure.com/models"  # Cleaned endpoint
# AZURE_MODEL_URL = "https://1lmhubpoc8598770946.openai.azure.com/openai/deployments/Ministral-3B/chat/completions?api-version=2024-02-15-preview"

def askAzureMinistral(question: str, context_chunks: List[Dict]) -> str:
    context = "\n\n".join(chunk["fields"].get("chunk_text", "") for chunk in context_chunks)
    prompt = f"Use the following context to answer the question:\n\n{context}\n\nQuestion: {question}"

    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }

    response = requests.post(AZURE_MODEL_URL, headers=headers, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]