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
    - Google Gemini (Google AI Studio & Vertex AI with GCP billing/ADC)
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
        is_vertex = (
            gemini_key == "vertex_adc_dummy_key"
            or bool(os.getenv("GCP_PROJECT_ID"))
            or bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            or os.path.exists("adc.json")
        )
        if is_vertex and gemini_key == "vertex_adc_dummy_key":
            return ("Vertex AI (ADC)", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        elif gemini_key:
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

        # 3. Check Google Gemini (AI Studio or Vertex AI via GCP ADC credits)
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        is_vertex = (
            gemini_key == "vertex_adc_dummy_key"
            or bool(os.getenv("GCP_PROJECT_ID"))
            or bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            or os.path.exists("adc.json")
        )
        if gemini_key or is_vertex:
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
            "  - Vertex AI (GCP credits): set GEMINI_API_KEY=vertex_adc_dummy_key and place adc.json in project root\n"
            "  - GEMINI_API_KEY (Free at https://aistudio.google.com)\n"
            "  - OLLAMA_URL (e.g. http://localhost:11434 for local free LLMs)\n"
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
        target_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Sanitize model name (e.g. gemini-3.1-pro doesn't exist, fall back to gemini-2.5-pro or 2.5-flash)
        if "3.1" in target_model or "preview" in target_model:
            target_model = "gemini-2.5-pro" if "pro" in target_model else "gemini-2.5-flash"

        # Check if using Vertex AI with ADC (GCP billing credits)
        is_vertex = (
            key == "vertex_adc_dummy_key"
            or bool(os.getenv("GCP_PROJECT_ID"))
            or bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            or os.path.exists("adc.json")
        )

        if is_vertex and (key == "vertex_adc_dummy_key" or not key):
            try:
                import google.auth
                from google.auth.transport.requests import Request as GoogleAuthRequest

                # Auto-detect local adc.json if GOOGLE_APPLICATION_CREDENTIALS is not explicitly set
                if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists("adc.json"):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("adc.json")

                credentials, default_project_id = google.auth.default()
                credentials.refresh(GoogleAuthRequest())

                # Resolve project ID
                project_id = os.getenv("GCP_PROJECT_ID", default_project_id)
                if not project_id and os.path.exists("adc.json"):
                    try:
                        with open("adc.json", "r") as f:
                            adc_data = json.load(f)
                            project_id = adc_data.get("project_id") or adc_data.get("quota_project_id")
                    except Exception:
                        pass

                if not project_id:
                    raise ValueError("Could not determine GCP_PROJECT_ID. Please set GCP_PROJECT_ID in your .env")

                location = os.getenv("GCP_LOCATION", "us-central1")
                vertex_model = target_model if target_model.startswith("google/") else f"google/{target_model}"

                endpoint = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/endpoints/openapi/chat/completions"
                payload = {
                    "model": vertex_model,
                    "messages": messages,
                    "temperature": temperature,
                    "safety_settings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
                    ]
                }
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json"
                }
                return await self._http_post(endpoint, headers, payload, "Vertex AI (ADC)")
            except ImportError as ie:
                raise RuntimeError(
                    f"Missing dependency for Vertex AI ADC: {str(ie)}. "
                    "Please install using: pip install google-auth requests"
                )
            except Exception as e:
                print(f"[!] [VERTEX ADC ERROR] {e}", file=sys.stderr)
                raise RuntimeError(f"Vertex AI ADC authentication failed: {str(e)}")

        # Default: Google AI Studio endpoint (expects API key starting with AIzaSy...)
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
        return await self._http_post(endpoint, headers, payload, "Gemini (AI Studio)")

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
