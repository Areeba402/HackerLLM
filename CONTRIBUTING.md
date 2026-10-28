# Contributing to HackerLLM

Thank you for your interest in contributing to **HackerLLM**! Community contributions are what make open-source security tools thrive.

## How to Contribute

### 1. Reporting Bugs
- Search existing GitHub Issues before opening a new one.
- Provide clear reproduction steps, environment details (OS, Docker version, Python version), and the exact tool output or logs.

### 2. Suggesting Enhancements
- Feature requests and suggestions for new offensive tool runners or LLM provider integrations are welcome.
- Describe the use case and why it benefits operators.

### 3. Code Contributions
1. Fork the repository.
2. Create a new branch: `git checkout -b feature/my-new-feature` or `git checkout -b fix/issue-description`.
3. Keep changes focused and clean. Avoid unnecessary dependencies.
4. Ensure code formatting is clean (PEP 8 for Python).
5. Commit with descriptive messages.
6. Push to your fork and submit a Pull Request.

## Code Standards
- Keep backend dependencies minimal. Do not add heavy database or ORM dependencies without discussion.
- All new execution wrappers must include timeouts and safe handling of subprocess outputs.
- Never hardcode API keys, credentials, or proprietary identifiers.
