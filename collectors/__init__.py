"""System metric collectors powered by psutil."""

from collectors.cpu import collect_cpu
from collectors.memory import collect_memory
from collectors.disk import collect_disk
from collectors.network import collect_network, NetworkRateTracker
from collectors.processes import collect_processes, top_processes, terminate_process
from collectors.battery import collect_battery
from collectors.system_info import collect_system_info

__all__ = [
    "collect_cpu",
    "collect_memory",
    "collect_disk",
    "collect_network",
    "NetworkRateTracker",
    "collect_processes",
    "top_processes",
    "terminate_process",
    "collect_battery",
    "collect_system_info",
]
