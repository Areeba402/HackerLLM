from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        model: str = None, 
        temperature: float = 0.2,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes a chat completion request and returns an OpenAI-standard response dictionary.
        """
        pass
