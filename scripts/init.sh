#!/bin/bash

# =============================================
# 🚀 WP Docker v2 - Init Script
# ---------------------------------------------
# - Load core.env & tiện ích bash
# - Tạo docker-compose.runtime.yml từ template
# - Hỗ trợ chế độ DEV với mount thư mục thực
# =============================================

# Gọi file load_config.sh
source "$(dirname "${BASH_SOURCE[0]}")/../core/bash-utils/load_config.sh"

# Load core.env và các hàm tiện ích
load_core_env || exit 1
load_core_utils

# =============================================
# 🧾 Kiểm tra file core.env, nếu chưa có thì copy từ sample
# =============================================

env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../core" && pwd)"
env_file="$env_dir/core.env"
env_sample="$env_dir/core.env.sample"

if ! _is_file_exist "$env_file"; then
    if _is_file_exist "$env_sample"; then
        copy_file "$env_sample" "$env_file" || exit 1
        echo "📋 Đã tạo file core.env từ mẫu"
    else
        echo "❌ Không tìm thấy core.env.sample!"
        exit 1
    fi
fi

# =============================================
# Khởi động Python Runtime Container
# ============================================
source "$(dirname "${BASH_SOURCE[0]}")/../scripts/init_python_runtime.sh"
_init_python_runtime || exit 1
echo "✅ Đã khởi động Python Runtime Container thành công."