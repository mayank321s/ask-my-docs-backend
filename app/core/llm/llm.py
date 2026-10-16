import os
import requests
from typing import List, Dict
import json
from huggingface_hub import InferenceClient
from typing import List, Dict, Optional, Tuple
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm.langchain_wrapper import HuggingFaceLLMWrapper
from app.core.llm.memory_utils import get_session_history

# URL of the locally running Ollama server (default port 11434)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")


def askOllamaLlm(question: str, context_chunks: List[Dict], model: str = "llama3.2:1b") -> str:
    """Send the question plus context to an Ollama-hosted model (default: Llama-3 7B).
Pass a different `model` arg to override."""

    # Build a single prompt that contains all context chunks
    context_parts = []
    for chunk in context_chunks:
        fields = chunk.get("fields", {})
        chunk_text = fields.get("chunk_text", "")

        metadata = {k: v for k, v in fields.items() if k != "chunk_text"}

        if metadata:
            meta_json = json.dumps(metadata, indent=2, default=str)
            metadata_str = f"\n[Metadata]\n{meta_json}\n"
        else:
            metadata_str = ""

        context_part = f"{chunk_text}{metadata_str}"
        context_parts.append(context_part)

    context = "\n\n".join(context_parts)

    prompt = (
        "You are a helpful and knowledgeable assistant.\n"
        "You have access to internal documents and data to help you answer questions.\n"
        "Based on the context below, answer the user's question clearly and conversationally, as if you're explaining from your own expertise.\n"
        "Also the date given which ever data is the latest that is updated information and the previous date is old information"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
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

def askOllamaLlmV2(question: str, context_chunks: List[Dict], model: str = "llama3.1") -> str:
    """Send the question plus context to an Ollama-hosted model (default: Llama-3 7B).
    Pass a different `model` arg to override."""

    # Build a single prompt that contains all context chunks
    context_parts = []
    for chunk in context_chunks:
        # Get metadata from Pinecone's QueryResponse structure
        metadata = chunk.get("metadata", {})
        chunk_text = metadata.get("chunk_text", "")
        
        # Extract other metadata (excluding chunk_text)
        other_metadata = {k: v for k, v in metadata.items() if k != "chunk_text"}
        
        # Include match score and ID for better context
        if "score" in chunk:
            other_metadata["relevance_score"] = chunk["score"]
        if "id" in chunk:
            other_metadata["chunk_id"] = chunk["id"]

        if other_metadata:
            meta_json = json.dumps(other_metadata, indent=2, default=str)
            metadata_str = f"\n[Metadata]\n{meta_json}\n"
        else:
            metadata_str = ""

        context_part = f"{chunk_text}{metadata_str}"
        context_parts.append(context_part)

    context = "\n\n".join(context_parts)

    prompt = (
        "You are a helpful and knowledgeable assistant.\n"
        "You have access to internal documents and data to help you answer questions.\n"
        "Based on the context below, answer the user's question clearly and conversationally, as if you're explaining from your own expertise.\n"
        "The data with the latest date represents updated information, while previous dates contain older information.\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
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
        return data.get("response", "")
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to query Ollama: {exc}") from exc

def askHuggingFaceLLM(question: str, context_chunks: List[Dict], model: str = "Qwen/Qwen2.5-7B-Instruct") -> str:
    """Send the question plus context to Hugging Face Together provider model (default: Qwen2.5-7B-Instruct).
    Pass a different `model` arg to override."""

    # Build a single prompt that contains all context chunks
    context_parts = []
    for chunk in context_chunks:
        fields = chunk.get("fields", {})
        chunk_text = fields.get("chunk_text", "")

        metadata = {k: v for k, v in fields.items() if k != "chunk_text"}

        if metadata:
            meta_json = json.dumps(metadata, indent=2, default=str)
            metadata_str = f"\n[Metadata]\n{meta_json}\n"
        else:
            metadata_str = ""

        context_part = f"{chunk_text}{metadata_str}"
        context_parts.append(context_part)

    context = "\n\n".join(context_parts)

    # Build the system message and user prompt
    system_message = (
        "You are a helpful and knowledgeable assistant. "
        "You have access to internal documents and data to help you answer questions. "
        "Based on the context provided, answer the user's question clearly and conversationally, "
        "as if you're explaining from your own expertise. "
        "Also the date given which ever data is the latest that is updated information and the previous date is old information."
    )

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    try:
        # Initialize client
        client = InferenceClient(
            provider="together",
            api_key=os.getenv("HF_TOKEN"),
        )
        
        # Create chat completion
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ],
            max_tokens=512,
            temperature=0.7
        )
        
        return completion.choices[0].message.content
        
    except Exception as exc:
        raise RuntimeError(f"Failed to query Hugging Face Together: {exc}") from exc

def askHuggingFaceLLMWithMemory(
    question: str, 
    context_chunks: List[Dict], 
    session_id: str = "default",
    model: str = "Qwen/Qwen2.5-7B-Instruct"
) -> Tuple[str, str]:
    """
    Ask HuggingFace LLM with conversation memory using modern LangChain approach.
    
    Args:
        question: User's question
        context_chunks: List of context chunks from vector search
        session_id: Session identifier for memory management
        model: Model name to use
        
    Returns:
        tuple: (answer, session_id)
    """
    # Build context string (same as your original logic)
    context_parts = []
    for chunk in context_chunks:
        fields = chunk.get("fields", {})
        chunk_text = fields.get("chunk_text", "")
        metadata = {k: v for k, v in fields.items() if k != "chunk_text"}
        
        if metadata:
            meta_json = json.dumps(metadata, indent=2, default=str)
            metadata_str = f"\n[Metadata]\n{meta_json}\n"
        else:
            metadata_str = ""
        
        context_part = f"{chunk_text}{metadata_str}"
        context_parts.append(context_part)

    context = "\n\n".join(context_parts)

    # Create the conversational chain
    conversational_chain = _get_or_create_runnable_chain(model)
    
    # Enhanced input with context
    enhanced_input = f"""Context:
{context}

Question: {question}"""
    
    # Run with session-based memory
    try:
        answer = conversational_chain.invoke(
            {"input": enhanced_input},
            config={"configurable": {"session_id": session_id}}
        )
        return answer, session_id
    except Exception as e:
        return f"Error processing with memory: {str(e)}", session_id

def _get_or_create_runnable_chain(model: str) -> RunnableWithMessageHistory:
    """Create RunnableWithMessageHistory chain (cached)."""
    # Use a simple cache mechanism
    cache_key = f"chain_{model}"
    
    if not hasattr(_get_or_create_runnable_chain, "chains"):
        _get_or_create_runnable_chain.chains = {}
    
    if cache_key not in _get_or_create_runnable_chain.chains:
        # Create HuggingFace LLM wrapper
        hf_llm = HuggingFaceLLMWrapper(model_name=model)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful and knowledgeable assistant. 
You have access to internal documents and data to help you answer questions. 
Based on the context provided, answer the user's question clearly and conversationally, 
as if you're explaining from your own expertise. 
The date given which ever data is the latest that is updated information and the previous date is old information."""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}")
        ])
        
        # Create the basic chain
        chain = prompt | hf_llm | StrOutputParser()
        
        # Wrap with message history
        conversational_chain = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        _get_or_create_runnable_chain.chains[cache_key] = conversational_chain
    
    return _get_or_create_runnable_chain.chains[cache_key]

def get_conversation_history(session_id: str) -> List[Dict]:
    """Get formatted conversation history for a session."""
    from app.core.llm.memory_utils import get_session_history
    
    history = get_session_history(session_id)
    formatted_history = []
    
    for message in history.messages:
        formatted_history.append({
            "type": message.type,  # "human" or "ai"
            "content": message.content,
            "timestamp": getattr(message, "timestamp", None)
        })
    
    return formatted_history

def clear_conversation_memory(session_id: str) -> bool:
    """Clear conversation memory for a session."""
    from app.core.llm.memory_utils import clear_session_history
    return clear_session_history(session_id)
