#!/bin/bash
# =============================================
# 🔧 Load Core Config + Tiện ích
# File: core/bash-utils/load_config.sh
# =============================================

# =============================================
# 🧾 Load biến môi trường từ core.env
# =============================================
load_core_env() {
    local this_dir
    this_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    local env_file="$this_dir/core/core.env"

    if [[ ! -f "$env_file" ]]; then
        echo "Config file not found: $env_file"
        return 1
    fi

    set -a
    source "$env_file"
    set +a
}

# =============================================
# 🧰 Load các tiện ích Bash quan trọng
# =============================================
load_core_utils() {
    local this_dir
    this_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

    source "$this_dir/core/bash-utils/validate.sh"
    source "$this_dir/core/bash-utils/get_path.sh"
    source "$this_dir/core/bash-utils/file_operations.sh"
    source "$this_dir/core/bash-utils/messages_utils.sh" 
    source "$this_dir/core/bash-utils/runtime_utils.sh" 
    source "$this_dir/core/bash-utils/docker_utils.sh"
}
