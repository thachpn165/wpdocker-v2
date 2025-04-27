import os
from core.backend.utils.debug import log_call

@log_call
def get_total_ram_mb():
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    return int(line.split()[1]) // 1024
    except FileNotFoundError:
        # fallback cho macOS (không có /proc)
        import subprocess
        output = subprocess.check_output(['sysctl', 'hw.memsize']).decode()
        return int(output.split(":")[1].strip()) // (1024 * 1024)
    return 1024

def get_total_cpu_cores():
    return os.cpu_count() or 2

