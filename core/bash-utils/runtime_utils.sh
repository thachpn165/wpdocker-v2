# =============================================
# 🐍 Gọi Python trong container runtime WP Docker
# ---------------------------------------------
# Kiểm tra container đã chạy trước khi exec
# =============================================
wpdocker_py() {
    local container="${CORE_RUNTIME_CONTAINER_NAME:-wpdocker-python-runtime}"

    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "❌ Container runtime ${container} chưa được khởi động."
        echo "👉 Hãy chạy: bash scripts/init.sh để khởi tạo hệ thống trước."
        return 1
    fi

    docker exec -it wpdocker-python-runtime python3 "$@"
}
