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

# Đảm bảo PYTHONPATH được thiết lập đúng trước khi chạy
export PYTHONPATH="$INSTALL_DIR"
echo "📊 Using PYTHONPATH: $PYTHONPATH"

"$PYTHON_EXEC" "$MAIN_FILE"