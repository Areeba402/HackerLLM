"""
GPT-OPS Universal Runner
Direct command execution engine for security tools inside Kali Linux.
"""

import shutil
import shlex
import re
from typing import Dict, Any
from utils.command_executor import execute

# Dangerous system-level commands that should not be run blindly
BLOCKED_TOOLS = {
    "dd", "shutdown", "reboot", "halt", "poweroff", 
    "mkfs", "rmdir", "fdisk", "parted"
}

# Tools that shouldn't have target auto-appended
NO_AUTO_TARGET = {
    "msfconsole", "searchsploit", "ls", "cat", "mkdir", "whoami", "id", 
    "echo", "grep", "find", "cp", "mv", "rm", "bash", "sh", "nc", 
    "curl", "wget", "python", "python3", "hydra", "medusa", "smbclient", 
    "sqlmap", "gobuster", "dirb", "wpscan", "nikto", "masscan", "katana", "ffuf"
}

def run_tool(tool_name: str, target: str, options: str = "", job_id: str = "default", timeout: int = 600, **kwargs) -> Dict[str, Any]:
    """
    Executes a security tool via subprocess inside the Kali Linux environment.
    """
    clean_tool = (tool_name or "").strip().lower()

    # 1. Security Check against system destruction
    if clean_tool in BLOCKED_TOOLS:
        return {
            "status": "error",
            "job_id": job_id,
            "tool": tool_name,
            "command": "",
            "output": f"Security restriction: Tool '{tool_name}' is blocked for safety.",
            "rc": 126
        }

    # Block destructive root deletion commands inside options
    if re.search(r"\brm\s+-[rf]{1,2}\s+/", options):
        return {
            "status": "error",
            "job_id": job_id,
            "tool": tool_name,
            "command": "",
            "output": "Security restriction: Destructive file operations are prohibited.",
            "rc": 126
        }

    # 2. Check if tool binary exists on system
    if not shutil.which(clean_tool) and clean_tool not in ("bash", "sh"):
        return {
            "status": "error",
            "job_id": job_id,
            "tool": tool_name,
            "command": "",
            "output": f"Error: '{tool_name}' is not installed or not in PATH inside the container.",
            "rc": 127
        }

    # 3. Construct Command
    # Handle recursive bash calling if options already start with bash -c
    opts = options.strip()
    if clean_tool in ("bash", "sh"):
        opts = re.sub(rf"^\s*{clean_tool}\s+(-c\s+)", r"\1", opts)
        if opts.startswith(f"{clean_tool} "):
            opts = opts[len(clean_tool):].strip()

    cmd = f"{clean_tool} {opts}".strip()

    # Only append target if needed and not already present in the command
    if target and clean_tool not in NO_AUTO_TARGET:
        if target not in cmd:
            cmd += f" {target}"

    print(f"[GPT-OPS:{job_id}] Executing: {cmd}", flush=True)

    # 4. Execute via Subprocess
    result = execute(cmd, timeout=timeout)
    if isinstance(result, tuple):
        raw_output, rc = result
    else:
        raw_output, rc = result, 0

    return {
        "status": "success" if rc == 0 else "error",
        "job_id": job_id,
        "tool": tool_name,
        "command": cmd,
        "output": str(raw_output or "Operation completed with no output."),
        "rc": rc
    }
