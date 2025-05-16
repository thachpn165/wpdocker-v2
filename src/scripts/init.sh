#!/bin/bash

set -e

# Đường dẫn cố định cho thư mục cài đặt
FIXED_INSTALL_DIR="/opt/wp-docker"

# Đường dẫn thực tế đến thư mục cài đặt (sẽ được sử dụng để tạo symlink nếu cần)
ACTUAL_INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Kiểm tra và tạo symlink chỉ khi không tồn tại /opt/wp-docker
if [ ! -e "$FIXED_INSTALL_DIR" ]; then
    echo "📁 Thư mục $FIXED_INSTALL_DIR không tồn tại"
    echo "🔗 Tạo symlink $FIXED_INSTALL_DIR -> $ACTUAL_INSTALL_DIR"
    
    # Kiểm tra thư mục cha có tồn tại không
    if [ ! -d "$(dirname "$FIXED_INSTALL_DIR")" ]; then
        echo "📁 Tạo thư mục $(dirname "$FIXED_INSTALL_DIR")"
        mkdir -p "$(dirname "$FIXED_INSTALL_DIR")"
    fi
    
    # Tạo symlink
    ln -sf "$ACTUAL_INSTALL_DIR" "$FIXED_INSTALL_DIR"
    echo "✅ Đã tạo symlink thành công"
else
    echo "✅ Thư mục $FIXED_INSTALL_DIR đã tồn tại, tiếp tục sử dụng"
fi

# Sử dụng đường dẫn cố định
INSTALL_DIR="$FIXED_INSTALL_DIR"
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

# Hiển thị thông tin môi trường để debug
echo "🔍 Thông tin môi trường Python:"
echo "Python path: $(which python3)"
echo "Virtual env Python: $PYTHON_EXEC"
echo "Virtualenv active: $VIRTUAL_ENV"

# Kiểm tra có thể import src không
echo "🔍 Kiểm tra khả năng import module src..."
if "$PYTHON_EXEC" -c "import src" 2>/dev/null; then
    echo "✅ Module src đã sẵn sàng để sử dụng"
else
    echo "⚠️ Không thể import module src, có thể cần cài đặt package"
    
    # Cài đặt package trong chế độ development nếu chưa cài đặt
    if [ -f "$INSTALL_DIR/setup.py" ]; then
        echo "📦 Cài đặt project trong chế độ development..."
        pip install -e "$INSTALL_DIR"
    fi
fi

# Chạy chương trình chính
cd "$INSTALL_DIR"  # Đảm bảo thư mục hiện tại là thư mục cài đặt
"$PYTHON_EXEC" "$MAIN_FILE"