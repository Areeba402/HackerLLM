# Supported LLM Providers & Setup Guide

HackerLLM is designed around a **Bring Your Own API (BYOAPI)** philosophy. You can use completely free local models, ultra-fast hosted APIs with free tiers, or standard frontier model APIs.

---

## 1. Google Gemini (Free Tier via AI Studio)

Google provides free access to Gemini Flash models via Google AI Studio.

### Setup:
1. Visit [Google AI Studio](https://aistudio.google.com).
2. Click **Get API key** and generate a free API key.
3. Configure your `.env`:
   ```ini
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODEL=gemini-2.0-flash
   ```

---

## 2. Ollama (100% Free, Private, Local)

[Ollama](https://ollama.ai) lets you run open-weights models (like Llama 3.1, Qwen 2.5 Coder, Mistral) locally on your own machine without sending any data to external servers.

### Setup:
1. Install Ollama from [ollama.ai](https://ollama.ai).
2. Pull your desired model:
   ```bash
   ollama pull llama3.1
   ```
3. Set your `.env`:
   ```ini
   # If running HackerLLM in Docker:
   OLLAMA_URL=http://host.docker.internal:11434
   OLLAMA_MODEL=llama3.1

   # If running HackerLLM locally:
   # OLLAMA_URL=http://localhost:11434
   ```

---

## 3. Groq Cloud (Free Tier Available, Ultra-Fast)

[Groq](https://groq.com) provides near-instant inference speeds for models like Llama 3.3 70B and Mixtral.

### Setup:
1. Sign up at [console.groq.com](https://console.groq.com).
2. Generate an API Key under **API Keys**.
3. Configure your `.env`:
   ```ini
   GROQ_API_KEY=gsk_...
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

---

## 4. OpenAI & OpenAI-Compatible Endpoints

HackerLLM supports OpenAI directly, as well as any provider using the OpenAI-compatible REST specification (DeepSeek, OpenRouter, Together AI, vLLM, LM Studio).

### Standard OpenAI:
```ini
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### DeepSeek:
```ini
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### OpenRouter:
```ini
OPENAI_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.3-70b-instruct
```

### Together AI:
```ini
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.together.xyz/v1
OPENAI_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

### Local LM Studio / vLLM:
```ini
OPENAI_BASE_URL=http://host.docker.internal:1234/v1
OPENAI_MODEL=local-model
```
