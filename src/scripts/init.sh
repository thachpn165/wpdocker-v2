#!/bin/bash

set -e

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$INSTALL_DIR/.venv"
PYTHON_EXEC="$VENV_DIR/bin/python"
MAIN_FILE="$INSTALL_DIR/src/main.py"

# Kiểm tra và tạo file core.env từ core.env.sample nếu cần
CORE_ENV="$INSTALL_DIR/core.env"
CORE_ENV_SAMPLE="$INSTALL_DIR/core.env.sample"

if [ ! -f "$CORE_ENV" ] && [ -f "$CORE_ENV_SAMPLE" ]; then
    echo "📄 Creating core.env from sample..."
    cp "$CORE_ENV_SAMPLE" "$CORE_ENV"
    echo "✅ Created core.env from sample template"
fi

# Kiểm tra python3
source "$(dirname "${BASH_SOURCE[0]}")/install_python.sh"
install_python

# Khởi tạo venv cho Python (tại thư mục .venv)
source "$(dirname "${BASH_SOURCE[0]}")/init_python.sh"
init_python_env

# Chạy backend
echo "🚀 Launching WP Docker..."

# Kích hoạt virtualenv trong shell hiện tại
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "🐍 Kích hoạt môi trường ảo Python trong shell chính..."
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️ Không tìm thấy tệp activate. Cố gắng tiếp tục mà không kích hoạt virtualenv..."
fi

# Đảm bảo PYTHONPATH được thiết lập đúng trước khi chạy
export PYTHONPATH="$INSTALL_DIR"
echo "📊 Using PYTHONPATH: $PYTHONPATH"

# Hiển thị thông tin môi trường để debug
echo "🔍 Thông tin môi trường Python:"
echo "Python path: $(which python3)"
echo "Virtual env Python: $PYTHON_EXEC"
echo "Virtualenv active: $VIRTUAL_ENV"

# Chạy chương trình chính
"$PYTHON_EXEC" "$MAIN_FILE"