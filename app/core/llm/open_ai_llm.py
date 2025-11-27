import os
import json
from typing import List, Dict, Tuple, AsyncGenerator
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
    model: str = os.getenv("OPENAI_MODEL")
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
            max_tokens=30000,
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
) -> Tuple[str, str]:
    """
    Ask OpenAI LLM with conversation memory using LangChain.
    
    Args:
        question: User's question
        context_chunks: List of context chunks from vector search
        session_id: Session identifier for memory management
        model: OpenAI model name (from OPENAI_MODEL env var)
    Returns:
        tuple: (answer, session_id)
    """
    # Build context string (same logic as askOpenAILLM)

    model: str = os.getenv("OPENAI_MODEL")
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
            max_tokens=30000,
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

async def askOpenAILLMWithMemoryStream(
    question: str, 
    context_chunks: List[Dict], 
    session_id: str = "default",
) -> AsyncGenerator[str, None]:
    """
    Stream responses from OpenAI LLM with conversation memory using LangChain.
    
    Args:
        question: User's question
        context_chunks: List of context chunks from vector search
        session_id: Session identifier for memory management
        
    Yields:
        str: Token chunks from the LLM response
    """
    model: str = os.getenv("OPENAI_MODEL")
    
    # Build context string
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
    
    # Get or create the conversational chain
    conversational_chain = _get_or_create_runnable_chain(model)
    
    # Enhanced input with context
    enhanced_input = f"""Context:
{context}

Question: {question}"""
    
    # Stream with session-based memory
    try:
        async for chunk in conversational_chain.astream(
            {"input": enhanced_input},
            config={"configurable": {"session_id": session_id}}
        ):
            if chunk:
                yield chunk
    except Exception as e:
        yield f"Error: {str(e)}"


async def askOpenAILLMStream(
    question: str, 
    context_chunks: List[Dict]
) -> AsyncGenerator[str, None]:
    """
    Stream responses from OpenAI LLM without memory.
    
    Args:
        question: User's question
        context_chunks: List of context chunks from vector search
        
    Yields:
        str: Token chunks from the LLM response
    """
    model: str = os.getenv("OPENAI_MODEL")
    
    # Build context string (same as with memory)
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
    
    # Create simple LLM without memory
    llm = ChatOpenAI(
        model=model,
        temperature=0.7,
        max_tokens=30000,
        streaming=True,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful and knowledgeable assistant. 
You have access to internal documents and data to help you answer questions. 
Based on the context provided, answer the user's question clearly and conversationally."""),
        ("human", "Context:\n{context}\n\nQuestion: {question}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        async for chunk in chain.astream({
            "context": context,
            "question": question
        }):
            if chunk:
                yield chunk
    except Exception as e:
        yield f"Error: {str(e)}"

async def askOpenAILLMWithMemoryStreamEvents(
    question: str, 
    context_chunks: List[Dict], 
    session_id: str = "default",
) -> AsyncGenerator[Dict, None]:
    """
    Stream events from OpenAI LLM with memory - provides more granular control.
    
    Yields:
        dict: Event data including tokens, metadata, and status updates
    """
    model: str = os.getenv("OPENAI_MODEL")
    
    # Build context (same as before)
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
    
    conversational_chain = _get_or_create_runnable_chain(model)
    
    enhanced_input = f"""Context:
{context}

Question: {question}"""
    
    try:
        async for event in conversational_chain.astream_events(
            {"input": enhanced_input},
            config={"configurable": {"session_id": session_id}},
            version="v2"
        ):
            # Filter for chat model streaming events
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield {
                        "type": "token",
                        "content": content
                    }
            elif event["event"] == "on_chat_model_start":
                yield {
                    "type": "model_start",
                    "message": "Model started generating"
                }
            elif event["event"] == "on_chat_model_end":
                yield {
                    "type": "model_end",
                    "message": "Model finished generating"
                }
    except Exception as e:
        yield {
            "type": "error",
            "message": str(e)
        }


import os
import json
from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI


def get_openai_client() -> AsyncOpenAI:
    """Get OpenAI client with custom base URL for AI Gateway."""
    api_key = os.getenv('AI_GATEWAY_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL', 'https://ai-gateway.vercel.sh/v1')
    
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url
    )


def format_chat_history(chat_history: List[Dict], limit: int = 5) -> List[Dict]:
    """
    Convert DB chat history to OpenAI messages format.
    Takes last N messages from history.
    """
    messages = []
    recent_history = chat_history[-limit:] if len(chat_history) > limit else chat_history
    
    for entry in recent_history:
        if "user" in entry:
            messages.append({"role": "user", "content": entry["user"]})
        if "assistant" in entry:
            messages.append({"role": "assistant", "content": entry["assistant"]})
    
    return messages


#     if chat_history:
#         formatted_history = format_chat_history(chat_history, limit=5)
    
#     # Add current question with context
#     messages.append({
#         "role": "user",
#         "content": f"""Previous Conversation History:
# {json.dumps(formatted_history, indent=2, default=str) if formatted_history else " "}
# Context:
# {context}


async def askOpenAILLMStreamUsingVercel(
    question: str, 
    context_chunks: List[Dict],
    chat_history: List[Dict] = None
) -> AsyncGenerator[str, None]:
    """
    Stream responses from OpenAI via Vercel AI Gateway in native SSE format.
    Returns complete JSON chunks in SSE format compatible with AI SDK.
    
    Args:
        question: User's current question
        context_chunks: List of context chunks from vector search
        chat_history: Optional chat history from DB
        
    Yields:
        str: SSE formatted strings with complete JSON chunks
    """
    model = os.getenv("OPENAI_MODEL", "gpt-4")
    client = get_openai_client()
    
    # Build context string
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
    
    # Build messages array
    messages = [
        {
            "role": "system",
            "content": """You are a helpful and knowledgeable assistant.
You have access to internal documents and data to help you answer questions.
Based on the context provided, answer the user's question clearly and conversationally."""
        }
    ]
    
    # Add chat history if provided
    formatted_history = ""
    if chat_history:
        formatted_history = format_chat_history(chat_history, limit=5)
    
    # Add current question with context
    messages.append({
        "role": "user",
        "content": f"""Previous Conversation History:
{json.dumps(formatted_history, indent=2, default=str) if formatted_history else " "}
Context:
{context}

Question: {question}"""
    })
    
    # Stream from OpenAI
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=30000
        )
        
        async for chunk in stream:
            # Convert chunk to dictionary
            chunk_dict = chunk.model_dump()
            
            # Format as SSE:  {json}\n\n
            sse_message = f" {json.dumps(chunk_dict)}\n\n"
            yield sse_message
        
        # Send the [DONE] message at the end
        yield " [DONE]\n\n"
                
    except Exception as e:
        # Send error in SSE format
        error_dict = {
            "error": {
                "message": str(e),
                "type": "api_error"
            }
        }
        yield f" {json.dumps(error_dict)}\n\n"
        yield " [DONE]\n\n"
