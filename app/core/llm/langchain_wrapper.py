# app/core/llm/langchain_wrapper.py
from langchain.llms.base import LLM
from typing import Any, List, Optional
from pydantic import Field
import os
from huggingface_hub import InferenceClient

class HuggingFaceLLMWrapper(LLM):
    """Custom LangChain wrapper for HuggingFace LLM"""
    
    # Properly declare as a Pydantic field
    model_name: str = Field(default="Qwen/Qwen2.5-7B-Instruct", description="HuggingFace model name")
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-7B-Instruct", **kwargs):
        super().__init__(model_name=model_name, **kwargs)
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        """Call the HuggingFace LLM directly."""
        try:
            return self._call_huggingface_direct(prompt)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _call_huggingface_direct(self, prompt: str) -> str:
        """Direct HuggingFace API call."""
        try:
            client = InferenceClient(
                provider="together",
                api_key=os.getenv("HF_TOKEN"),
            )
            
            completion = client.chat.completions.create(
                model=self.model_name,  # This should work now
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful and knowledgeable assistant."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=512,
                temperature=0.7
            )
            
            return completion.choices[0].message.content
            
        except Exception as exc:
            raise RuntimeError(f"Failed to query Hugging Face Together: {exc}") from exc

    @property
    def _llm_type(self) -> str:
        return "huggingface_together"

    @property
    def _identifying_params(self) -> dict:
        return {"model_name": self.model_name}
