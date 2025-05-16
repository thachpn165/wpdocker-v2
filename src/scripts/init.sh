#!/bin/bash

set -e

# Đường dẫn cố định cho thư mục cài đặt
FIXED_INSTALL_DIR="/opt/wp-docker"

# Đường dẫn thực tế đến thư mục cài đặt (sẽ được sử dụng để tạo symlink nếu cần)
ACTUAL_INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Kiểm tra và tạo symlink nếu cần
if [ ! -e "$FIXED_INSTALL_DIR" ]; then
    echo "🔗 Tạo symlink $FIXED_INSTALL_DIR -> $ACTUAL_INSTALL_DIR"
    # Kiểm tra thư mục cha có tồn tại không
    if [ ! -d "$(dirname "$FIXED_INSTALL_DIR")" ]; then
        echo "📁 Tạo thư mục $(dirname "$FIXED_INSTALL_DIR")"
        mkdir -p "$(dirname "$FIXED_INSTALL_DIR")"
    fi
    ln -sf "$ACTUAL_INSTALL_DIR" "$FIXED_INSTALL_DIR"
    echo "✅ Đã tạo symlink thành công"
elif [ -L "$FIXED_INSTALL_DIR" ]; then
    # Đã là symlink, kiểm tra đích
    LINK_TARGET=$(readlink "$FIXED_INSTALL_DIR")
    if [ "$LINK_TARGET" != "$ACTUAL_INSTALL_DIR" ]; then
        echo "⚠️ Symlink $FIXED_INSTALL_DIR đang trỏ đến $LINK_TARGET"
        echo "🔄 Cập nhật symlink để trỏ đến $ACTUAL_INSTALL_DIR"
        ln -sf "$ACTUAL_INSTALL_DIR" "$FIXED_INSTALL_DIR"
        echo "✅ Đã cập nhật symlink thành công"
    else
        echo "✅ Symlink $FIXED_INSTALL_DIR đã trỏ đúng đến $ACTUAL_INSTALL_DIR"
    fi
elif [ -d "$FIXED_INSTALL_DIR" ]; then
    # Là thư mục bình thường, không phải symlink
    echo "⚠️ $FIXED_INSTALL_DIR đã tồn tại và không phải là symlink"
    echo "🔍 Kiểm tra xem có phải thư mục cài đặt hiện tại không..."
    
    # Nếu là cùng đường dẫn thật sự, mọi thứ OK
    if [ "$(cd "$FIXED_INSTALL_DIR" && pwd)" = "$(cd "$ACTUAL_INSTALL_DIR" && pwd)" ]; then
        echo "✅ $FIXED_INSTALL_DIR là thư mục cài đặt hiện tại, tiếp tục"
    else
        echo "❌ $FIXED_INSTALL_DIR không phải là thư mục cài đặt hiện tại"
        echo "⚠️ Vui lòng xóa hoặc di chuyển thư mục $FIXED_INSTALL_DIR và chạy lại script"
        exit 1
    fi
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

# Đảm bảo PYTHONPATH được thiết lập đúng trước khi chạy
export PYTHONPATH="$INSTALL_DIR:$ACTUAL_INSTALL_DIR"
echo "📊 Using PYTHONPATH: $PYTHONPATH"

# Tạo file init.py nếu cần thiết (đảm bảo các thư mục được nhận diện là package Python)
# Đặc biệt quan trọng cho symlink trên Linux
check_init_file() {
    local dir="$1"
    if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then
        echo "📦 Tạo file __init__.py trong $dir"
        touch "$dir/__init__.py"
    fi
}

echo "🔍 Kiểm tra và đảm bảo các module Python hoạt động đúng..."

# Chỉ kiểm tra các thư mục con của common nếu không tìm thấy common.config
if ! python3 -c "import src.common.config" 2>/dev/null; then
    echo "⚠️ Không tìm thấy module src.common.config, kiểm tra cấu trúc package..."
    COMMON_CONFIG_DIR="$INSTALL_DIR/src/common/config"
    mkdir -p "$COMMON_CONFIG_DIR"
    check_init_file "$INSTALL_DIR/src"
    check_init_file "$INSTALL_DIR/src/common"
    check_init_file "$COMMON_CONFIG_DIR"
    
    # Kiểm tra có file quản lý cấu hình không
    if [ ! -f "$COMMON_CONFIG_DIR/manager.py" ]; then
        echo "🔄 Sao chép file manager.py từ thư mục gốc..."
        if [ -f "$ACTUAL_INSTALL_DIR/src/common/config/manager.py" ]; then
            cp "$ACTUAL_INSTALL_DIR/src/common/config/manager.py" "$COMMON_CONFIG_DIR/"
        fi
    fi
fi

# Thử một cách khác: sử dụng PYTHONPATH tương đối
# Thêm thư mục src vào PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$INSTALL_DIR/src"
echo "📊 Updated PYTHONPATH: $PYTHONPATH"

# Hiển thị thông tin môi trường để debug
echo "🔍 Thông tin môi trường Python:"
echo "Python path: $(which python3)"
echo "Virtual env Python: $PYTHON_EXEC"
echo "Virtualenv active: $VIRTUAL_ENV"

# Chạy chương trình chính với tùy chọn đặc biệt - điều chỉnh sys.path
"$PYTHON_EXEC" -c "
import sys, os
sys.path.insert(0, '$INSTALL_DIR')
sys.path.insert(0, '$ACTUAL_INSTALL_DIR')

# Kiểm tra sys.path
print('Python sys.path:')
for p in sys.path[:5]:
    print(f'  - {p}')

# Kiểm tra module
try:
    import src
    print('✅ Module src loaded successfully')
except ImportError as e:
    print(f'❌ Failed to load src: {e}')

# Chạy chương trình chính
try:
    sys.argv[0] = '$MAIN_FILE'
    exec(open('$MAIN_FILE').read())
except Exception as e:
    print(f'❌ Error running main program: {e}')
"