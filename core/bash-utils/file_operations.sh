#!/bin/bash
# =============================================
# 📁 File Operations - WP Docker v2
# File: core/bash-utils/file_operations.sh
# =============================================

# Yêu cầu hàm kiểm tra file tồn tại
source "$(dirname "${BASH_SOURCE[0]}")/validate.sh"

# =============================================
# 📄 copy_file <source_file> <destination_file>
# ---------------------------------------------
# Copy file từ nguồn đến đích sau khi kiểm tra hợp lệ
# =============================================
copy_file() {
    local src="$1"
    local dest="$2"

    if ! _is_file_exist "$src"; then
        echo "Không thể copy, file nguồn không hợp lệ: $src"
        return 1
    fi

    cp "$src" "$dest"
    if [[ $? -ne 0 ]]; then
        echo "Lỗi khi sao chép file từ $src đến $dest"
        return 1
    fi

    echo "📋 Đã sao chép file: $src → $dest"
    return 0
}
