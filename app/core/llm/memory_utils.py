# app/core/llm/memory_utils.py
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict
from app.core.llm.langchain_wrapper import HuggingFaceLLMWrapper

# Global storage for conversation histories
_conversation_store: Dict[str, InMemoryChatMessageHistory] = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Get or create chat history for a session."""
    if session_id not in _conversation_store:
        _conversation_store[session_id] = InMemoryChatMessageHistory()
    return _conversation_store[session_id]

def clear_session_history(session_id: str) -> bool:
    """Clear chat history for a specific session."""
    if session_id in _conversation_store:
        del _conversation_store[session_id]
        return True
    return False

def get_all_sessions() -> list:
    """Get all active session IDs."""
    return list(_conversation_store.keys())

def get_session_message_count(session_id: str) -> int:
    """Get number of messages in a session."""
    if session_id in _conversation_store:
        return len(_conversation_store[session_id].messages)
    return 0
