import psutil
import platform
from rich.console import Console
from rich.table import Table
import subprocess
import sys


def get_full_cpu_name() -> str:
    try:
        if sys.platform == "darwin":
            # macOS
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        elif sys.platform.startswith("linux"):
            # Linux
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        # Fallback
        cpu_name = platform.processor() or platform.uname().processor or platform.uname().machine
        return cpu_name
    except Exception:
        return "Unknown"


def show_system_info_table(console=None):
    if console is None:
        console = Console()
    # CPU Name & Frequency
    try:
        cpu_name = get_full_cpu_name()
        freq = psutil.cpu_freq()
        if freq:
            cpu_freq = f"{freq.current:.0f} MHz"
            if freq.max and freq.max != freq.current:
                cpu_freq += f" (max {freq.max:.0f} MHz)"
        else:
            cpu_freq = "Unknown"
    except Exception:
        cpu_name = "Unknown"
        cpu_freq = "Unknown"
    # RAM usage
    try:
        vm = psutil.virtual_memory()
        ram_used = f"{vm.used / (1024**3):.1f} GB"
        ram_total = f"{vm.total / (1024**3):.1f} GB"
        ram_str = f"{ram_used} / {ram_total}"
    except Exception:
        ram_str = "Unknown"
    # Disk usage
    try:
        du = psutil.disk_usage('/')
        disk_used = f"{du.used / (1024**3):.1f} GB"
        disk_total = f"{du.total / (1024**3):.1f} GB"
        disk_str = f"{disk_used} / {disk_total}"
    except Exception:
        disk_str = "Unknown"
    # Docker usage
    docker_images = docker_containers = docker_volumes = "?"
    try:
        docker_df = subprocess.check_output(["docker", "system", "df", "--format", "{{json .}}"]).decode().splitlines()
        for line in docker_df:
            import json
            data = json.loads(line)
            if data["Type"] == "Images":
                docker_images = data["Size"]
            elif data["Type"] == "Containers":
                docker_containers = data["Size"]
            elif data["Type"] == "Local Volumes":
                docker_volumes = data["Size"]
    except Exception:
        pass
    # Display table
    table = Table(title="System Information", show_header=True, header_style="bold magenta")
    table.add_column("Info", style="bold")
    table.add_column("Value", style="cyan")
    table.add_row("CPU", cpu_name)
    table.add_row("CPU Frequency", cpu_freq)
    table.add_row("RAM", ram_str)
    table.add_row("Disk (root)", disk_str)
    table.add_row("Docker Images", docker_images)
    table.add_row("Docker Containers", docker_containers)
    table.add_row("Docker Volumes", docker_volumes)
    console.print(table)
