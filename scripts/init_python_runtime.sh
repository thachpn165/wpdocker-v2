#!/bin/bash
# =============================================
# 🐍 Init Python Runtime Container
# File: core/bash-utils/init_python_runtime.sh
# =============================================



_init_python_runtime() {
    # =============================================
    # 📦 Xác định RUNTIME_MOUNT_SOURCE_DIR
    # =============================================
    RUNTIME_MOUNT_SOURCE_DIR="$INSTALL_DIR"

    if [[ "$DEV_MODE" == "true" || -f "$INSTALL_DIR/.dev" ]]; then
        RUNTIME_MOUNT_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
        echo "🧪 DEV MODE: mount từ thư mục $RUNTIME_MOUNT_SOURCE_DIR"
    fi

    export RUNTIME_MOUNT_SOURCE_DIR
    export INSTALL_DIR
    export PROJECT_NAME
    export CORE_RUNTIME_IMAGES
    export CORE_RUNTIME_CONTAINER_NAME

    # =============================================
    # 🛠 Render docker-compose.runtime.yml
    # =============================================
    local template_path
    template_path="$(get_path_templates)/docker-compose.runtime.yml.template"
    local compose_dir
    compose_dir="$(get_path_docker_compose)"
    local output_path="$compose_dir/docker-compose.runtime.yml"

    mkdir -p "$compose_dir"

    if ! _is_file_exist "$template_path"; then
        echo "❌ Không tìm thấy template: $template_path"
        return 1
    fi

    envsubst <"$template_path" >"$output_path"
    echo "✅ Đã tạo file: $output_path"

    # =============================================
    # 🚀 Khởi động container nếu chưa chạy
    # =============================================
    local container_name="$CORE_RUNTIME_CONTAINER_NAME"

    if docker ps --format '{{.Names}}' | grep -q "^$container_name$"; then
        echo "✅ Container $container_name đã chạy."
    else
        echo "🔧 Đang khởi động container $container_name..."
        docker compose -f "$output_path" up -d
        if [[ $? -eq 0 ]]; then
            echo "✅ Container đã được khởi động thành công."
        else
            echo "❌ Lỗi khi khởi động container runtime!"
            return 1
        fi
    fi
}
