import os
import sys
import json
import httpx
from typing import Dict, Any, List, Optional, Tuple
from .base import BaseLLMProvider

class LLMManager:
    """
    Unified manager routing chat requests to supported LLM platforms:
    - Ollama (Local & 100% Free)
    - Google Gemini (Free tier available)
    - Groq (Free tier available, ultra-fast)
    - OpenAI / OpenAI-Compatible (DeepSeek, OpenRouter, Together AI, vLLM, LM Studio)
    """

    def __init__(self):
        self.default_timeout = 180.0

    def detect_active_provider(self, client_key: Optional[str] = None) -> Tuple[str, str]:
        """
        Detects which LLM provider is currently active based on environment variables or client key.
        Returns: (provider_name, model_name)
        """
        ollama_url = os.getenv("OLLAMA_URL", "").strip()
        if ollama_url:
            return ("Ollama", os.getenv("OLLAMA_MODEL", "llama3.1"))

        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            return ("Groq", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))

        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            return ("Gemini", os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

        openai_key = client_key or os.getenv("OPENAI_API_KEY", "").strip()
        openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        if openai_key or (openai_base and "openai.com" not in openai_base):
            return ("OpenAI-Compatible", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

        return ("None", "None")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        client_api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Routes the request to the configured backend provider.
        """
        # 1. Check Ollama (Local free instance)
        ollama_url = os.getenv("OLLAMA_URL", "").strip()
        if ollama_url:
            return await self._call_ollama(messages, model, temperature, ollama_url)

        # 2. Check Groq (Ultra-fast free tier)
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            return await self._call_groq(messages, model, temperature, groq_key)

        # 3. Check Google Gemini (Free tier via Google AI Studio)
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            return await self._call_gemini(messages, model, temperature, gemini_key)

        # 4. Check OpenAI or custom OpenAI-compatible endpoint
        openai_key = client_api_key or os.getenv("OPENAI_API_KEY", "").strip()
        openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        
        if openai_key or (openai_base and "openai.com" not in openai_base):
            return await self._call_openai_compatible(
                messages, model, temperature, openai_key, openai_base
            )

        raise ValueError(
            "No LLM provider configured! Please set one of the following in your .env file:\n"
            "  - OLLAMA_URL (e.g. http://localhost:11434 for local free LLMs)\n"
            "  - GEMINI_API_KEY (Free at https://aistudio.google.com)\n"
            "  - GROQ_API_KEY (Free at https://console.groq.com)\n"
            "  - OPENAI_API_KEY (from OpenAI, DeepSeek, or any compatible provider)"
        )

    async def _call_ollama(
        self, messages: List[Dict[str, Any]], model: Optional[str], temperature: float, url: str
    ) -> Dict[str, Any]:
        target_model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        endpoint = f"{url.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature
        }
        headers = {"Content-Type": "application/json"}
        return await self._http_post(endpoint, headers, payload, "Ollama")

    async def _call_groq(
        self, messages: List[Dict[str, Any]], model: Optional[str], temperature: float, key: str
    ) -> Dict[str, Any]:
        target_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        return await self._http_post(endpoint, headers, payload, "Groq")

    async def _call_gemini(
        self, messages: List[Dict[str, Any]], model: Optional[str], temperature: float, key: str
    ) -> Dict[str, Any]:
        target_model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        return await self._http_post(endpoint, headers, payload, "Gemini")

    async def _call_openai_compatible(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str],
        temperature: float,
        key: str,
        base_url: str
    ) -> Dict[str, Any]:
        target_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature
        }
        headers = {
            "Authorization": f"Bearer {key}" if key else "",
            "Content-Type": "application/json"
        }
        return await self._http_post(endpoint, headers, payload, "OpenAI-Compatible")

    async def _http_post(
        self, endpoint: str, headers: Dict[str, str], payload: Dict[str, Any], provider_name: str
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.default_timeout) as client:
            try:
                res = await client.post(endpoint, headers=headers, json=payload)
                if res.status_code >= 400:
                    err_msg = f"{provider_name} returned status {res.status_code}: {res.text[:300]}"
                    print(f"[!] [LLM ERROR] {err_msg}", file=sys.stderr)
                    raise RuntimeError(err_msg)
                return res.json()
            except httpx.RequestError as e:
                err_msg = f"Failed to connect to {provider_name} at {endpoint}: {str(e)}"
                print(f"[!] [LLM CONNECTION ERROR] {err_msg}", file=sys.stderr)
                raise RuntimeError(err_msg)
