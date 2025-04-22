"""Process list collector."""

from __future__ import annotations

from typing import List, Optional, Tuple

import psutil

from models import ProcessInfo


def collect_processes() -> List[ProcessInfo]:
    """Enumerate processes with CPU and memory usage.

    Calls cpu_percent(None) which is relative to the previous call on each
    Process object. First pass after process creation often returns 0.
    """
    results: List[ProcessInfo] = []
    attrs = ["pid", "name", "cpu_percent", "memory_info", "memory_percent", "status", "username"]

    for proc in psutil.process_iter(attrs=attrs, ad_value=None):
        try:
            info = proc.info
            mem_info = info.get("memory_info")
            rss = int(mem_info.rss) if mem_info is not None else 0
            results.append(
                ProcessInfo(
                    pid=int(info["pid"]),
                    name=str(info.get("name") or "unknown"),
                    cpu_percent=float(info.get("cpu_percent") or 0.0),
                    memory_rss=rss,
                    memory_percent=float(info.get("memory_percent") or 0.0),
                    status=str(info.get("status") or ""),
                    username=str(info.get("username") or ""),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return results


def top_processes(
    processes: Optional[List[ProcessInfo]] = None,
    limit: int = 10,
    sort_by: str = "cpu",
) -> List[ProcessInfo]:
    procs = processes if processes is not None else collect_processes()
    key = (lambda p: p.cpu_percent) if sort_by == "cpu" else (lambda p: p.memory_rss)
    return sorted(procs, key=key, reverse=True)[:limit]


def terminate_process(pid: int) -> Tuple[bool, str]:
    """Attempt to terminate a process. Returns (ok, message)."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()
        return True, f"Terminated {name} (PID {pid})"
    except psutil.NoSuchProcess:
        return False, f"Process {pid} no longer exists"
    except psutil.AccessDenied:
        return False, f"Permission denied terminating PID {pid}"
    except Exception as exc:  # noqa: BLE001 — surface to UI
        return False, str(exc)
