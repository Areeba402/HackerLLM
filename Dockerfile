# ==============================================================================
# HackerLLM: An AI-powered cybersecurity agent that turns natural language
# into real security tool execution.
# Kali Linux Container with Security Arsenal & API Gateway
# ==============================================================================

FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# 1. Update and install core Kali CLI tools and Python runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    kali-linux-headless \
    wordlists \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    golang-go \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Install ProjectDiscovery Nuclei (Vulnerability Scanner) & Katana (Crawler)
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    cp /root/go/bin/nuclei /usr/local/bin/nuclei && \
    nuclei -update-templates 2>/dev/null || true && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    cp /root/go/bin/katana /usr/local/bin/katana && \
    rm -rf /root/go

# 3. Setup Python Virtual Environment
WORKDIR /app
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 4. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy project files
COPY . .

# 6. Expose Gateway Port
EXPOSE 5000

# 7. Start HackerLLM API Server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
