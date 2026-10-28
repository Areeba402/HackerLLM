import subprocess
import threading
import time
import queue
import shlex
from typing import Union, List, Tuple

def execute(
    command: Union[str, List[str]], 
    timeout: int = 600, 
    abort_on_patterns: list = None
) -> Tuple[str, int]:
    """
    Executes a shell command or list and captures combined stdout/stderr.
    
    Args:
        command: Shell command string or argument list.
        timeout: Max execution time in seconds (default: 10 minutes).
        abort_on_patterns: List of substrings that trigger immediate process kill.
    
    Returns:
        tuple: (output_string, return_code)
               return_code 0 = success, non-zero = failure,
               -1 = timeout/aborted, -2 = exception.
    """
    if abort_on_patterns is None:
        abort_on_patterns = [
            "segmentation fault",
            "traceback (most recent call last)"
        ]

    patterns_lower = [p.lower() for p in abort_on_patterns]
    is_shell = True
    cmd_to_run = command

    if isinstance(command, list):
        is_shell = False
        cmd_to_run = command
    elif isinstance(command, str):
        meta_chars = [';', '&', '|', '>', '<', '`', '\n', '$', '(', ')']
        has_meta = any(char in command for char in meta_chars)
        if not has_meta:
            try:
                cmd_to_run = shlex.split(command)
                is_shell = False
            except Exception:
                is_shell = True
                cmd_to_run = command
        else:
            is_shell = True
            cmd_to_run = command

    try:
        proc = subprocess.Popen(
            cmd_to_run,
            shell=is_shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        out_q = queue.Queue()

        def reader(stream, tag):
            try:
                for line in iter(stream.readline, ''):
                    out_q.put((tag, line))
            except (ValueError, OSError):
                pass
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

        t_out = threading.Thread(target=reader, args=(proc.stdout, 'OUT'), daemon=True)
        t_err = threading.Thread(target=reader, args=(proc.stderr, 'ERR'), daemon=True)
        t_out.start()
        t_err.start()

        start = time.time()
        collected_out = []
        collected_err = []

        while True:
            try:
                tag, line = out_q.get(timeout=0.3)
            except queue.Empty:
                tag, line = None, None

            if tag and line is not None:
                if tag == 'OUT':
                    collected_out.append(line)
                else:
                    collected_err.append(line)

                if patterns_lower:
                    line_lower = line.lower()
                    for pat in patterns_lower:
                        if pat in line_lower:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                            output = "".join(collected_out) + "\n[STDERR]\n" + "".join(collected_err)
                            return (output.strip(), -1)

            if proc.poll() is not None:
                t_out.join(timeout=1.5)
                t_err.join(timeout=1.5)

                while not out_q.empty():
                    try:
                        tag, line = out_q.get_nowait()
                        if tag == 'OUT':
                            collected_out.append(line)
                        else:
                            collected_err.append(line)
                    except queue.Empty:
                        break

                rc = proc.returncode
                output = "".join(collected_out)
                if collected_err:
                    output += f"\n[STDERR]\n{''.join(collected_err)}"
                return (output.strip() if output.strip() else "Operation completed with no output.", rc)

            if time.time() - start > timeout:
                try:
                    proc.kill()
                    proc.wait(timeout=3)
                except Exception:
                    pass
                output = "".join(collected_out)
                if collected_err:
                    output += f"\n[STDERR]\n{''.join(collected_err)}"
                return (f"Error: Process timed out after {timeout} seconds.\n" + output.strip(), -1)

            time.sleep(0.02)

    except Exception as e:
        return (f"Runtime Execution Exception: {str(e)}", -2)
