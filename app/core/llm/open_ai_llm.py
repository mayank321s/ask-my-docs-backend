import os
import json
from typing import List, Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory import ChatMessageHistory

session_store = {}

gpt_model = os.getenv("OPENAI_MODEL")

def get_session_history(session_id: str) -> ChatMessageHistory:
    """Get or create chat message history for a session."""
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

def clear_session_history(session_id: str) -> bool:
    """Clear conversation memory for a session."""
    if session_id in session_store:
        session_store[session_id].clear()
        del session_store[session_id]
        return True
    return False


def askOpenAILLM(
    question: str, 
    context_chunks: List[Dict], 
    model: str = os.getenv("OPENAI_MODEL")
) -> str:
    """
    Send the question plus context to OpenAI GPT model.
    
    Args:
        question: User's question
        context_chunks: List of context chunks from vector search
        model: OpenAI model name (default: gpt-4o)
        
    Returns:
        str: Answer from the model
    """
    # Build context string from chunks
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
        "The date given which ever data is the latest that is updated information and the previous date is old information."
    )
    
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    
    try:
        # Initialize OpenAI client
        llm = ChatOpenAI(
            model=model,
            temperature=0.7,
            max_tokens=512,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create messages
        messages = [
            ("system", system_message),
            ("human", user_prompt)
        ]
        
        # Get response
        response = llm.invoke(messages)
        return response.content
        
    except Exception as exc:
        raise RuntimeError(f"Failed to query OpenAI: {exc}") from exc


def askOpenAILLMWithMemory(
    question: str, 
    context_chunks: List[Dict], 
    session_id: str = "default",
    model: str = os.getenv("OPENAI_MODEL")
) -> Tuple[str, str]:
    """
    Ask OpenAI LLM with conversation memory using LangChain.
    
    Args:
        question: User's question
        context_chunks: List of context chunks from vector search
        session_id: Session identifier for memory management
        model: OpenAI model name (default: gpt-4o)
        
    Returns:
        tuple: (answer, session_id)
    """
    # Build context string (same logic as askOpenAILLM)
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
    
    # Create the conversational chain with memory
    conversational_chain = _get_or_create_runnable_chain(model)
    
    # Enhanced input with context
    enhanced_input = f"""Context:
{context}

Question: {question}"""
    
    # Run with session-based memory
    try:
        response = conversational_chain.invoke(
            {"input": enhanced_input},
            config={"configurable": {"session_id": session_id}}
        )
        return response, session_id
    except Exception as e:
        return f"Error processing with memory: {str(e)}", session_id


def _get_or_create_runnable_chain(model: str) -> RunnableWithMessageHistory:
    """
    Create RunnableWithMessageHistory chain for OpenAI (cached).
    
    Args:
        model: OpenAI model name
        
    Returns:
        RunnableWithMessageHistory: Conversational chain with memory
    """
    # Simple cache mechanism
    cache_key = f"openai_chain_{model}"
    
    if not hasattr(_get_or_create_runnable_chain, "chains"):
        _get_or_create_runnable_chain.chains = {}
    
    if cache_key not in _get_or_create_runnable_chain.chains:
        # Create OpenAI LLM
        llm = ChatOpenAI(
            model=model,
            temperature=0.7,
            max_tokens=512,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful and knowledgeable assistant. 
You have access to internal documents and data to help you answer questions. 
Based on the context provided, answer the user's question clearly and conversationally, 
as if you're explaining from your own expertise. 
The date given which ever data is the latest that is updated information and the previous date is old information."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # Create the basic chain
        chain = prompt | llm | StrOutputParser()
        
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
    """
    Get formatted conversation history for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List[Dict]: Formatted conversation history
    """
    history = get_session_history(session_id)
    formatted_history = []
    
    for message in history.messages:
        formatted_history.append({
            "type": message.type,  # "human" or "ai"
            "content": message.content,
            "timestamp": getattr(message, "timestamp", None)
        })
    
    return formatted_history
