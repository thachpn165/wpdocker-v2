#!/bin/bash
# =============================================
# ✅ Validation Helpers - WP Docker v2
# File: core/bash-utils/validate.sh
# ---------------------------------------------
# Chứa các hàm kiểm tra file, thư mục, và quyền
# =============================================

# ========================
# 📄 _is_file_exist <file_path>
# ========================
# Kiểm tra file có tồn tại và có thể đọc/ghi
# ========================
_is_file_exist() {
    local file="$1"

    if [[ ! -e "$file" ]]; then
        echo "❌ File không tồn tại: $file"
        return 1
    fi

    if [[ ! -f "$file" ]]; then
        echo "❌ Không phải là file hợp lệ: $file"
        return 1
    fi

    if [[ ! -r "$file" ]]; then
        echo "❌ Không có quyền đọc file: $file"
        return 1
    fi

    if [[ ! -w "$file" ]]; then
        echo "⚠️ Không có quyền ghi file (vẫn có thể đọc được): $file"
    fi

    return 0
}

# ========================
# 📁 _is_dir_exist <dir_path>
# ========================
# Kiểm tra thư mục có tồn tại không
# ========================
_is_dir_exist() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        echo "❌ Thư mục không tồn tại: $dir"
        return 1
    fi

    return 0
}
