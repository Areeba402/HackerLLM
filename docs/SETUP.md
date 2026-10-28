# HackerLLM Installation & Setup Guide

This guide walks through setting up HackerLLM on Linux, macOS, or Windows.

---

## Prerequisites

- **Docker & Docker Compose** (Recommended): [Get Docker](https://docs.docker.com/get-docker/)
- OR **Kali Linux / Debian / Ubuntu** with Python 3.10+ if running directly on bare metal.

---

## Method A: Running via Docker (Recommended)

Running via Docker ensures you have all Kali tools pre-installed and isolated from your host system.

1. **Clone the Repo:**
   ```bash
   git clone https://github.com/<your-username>/hackerllm.git
   cd hackerllm
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and specify your LLM credentials (e.g. Gemini, Groq, Ollama, or OpenAI).

3. **Build and Run:**
   ```bash
   docker compose up --build -d
   ```

4. **Access the Console:**
   Open your browser to `http://localhost:5000`.

5. **View Logs or Stop:**
   ```bash
   # View logs
   docker compose logs -f hackerllm

   # Stop container
   docker compose down
   ```

---

## Method B: Native Kali Linux Installation

If you are already running Kali Linux as your primary OS or in a virtual machine:

1. **Install Python venv & dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip
   ```

2. **Setup virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your favorite LLM credentials
   ```

4. **Start the API Server:**
   ```bash
   python3 app.py
   ```
   The web interface will be available at `http://localhost:5000`.

---

## Troubleshooting

### "Tool not found" error
If you are running natively (outside Docker), make sure the tool (e.g., `nmap`, `sqlmap`, `nuclei`) is installed and available in your `$PATH`.

### Port 5000 Already in Use
You can change the listening port in `.env`:
```ini
PORT=5050
```
Then access `http://localhost:5050`.
