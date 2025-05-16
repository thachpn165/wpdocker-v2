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

# Tạo file init.py với nội dung phù hợp (đảm bảo các thư mục được nhận diện là package Python)
# Đặc biệt quan trọng cho symlink trên Linux
create_init_file() {
    local dir="$1"
    local content="$2"
    
    if [ -d "$dir" ]; then
        if [ ! -f "$dir/__init__.py" ] || [ -z "$(cat "$dir/__init__.py")" ]; then
            echo "📦 Tạo file __init__.py trong $dir"
            echo "$content" > "$dir/__init__.py"
            echo "✅ Đã tạo $dir/__init__.py với nội dung phù hợp"
        else
            echo "✅ File $dir/__init__.py đã tồn tại"
        fi
    else
        echo "📁 Tạo thư mục $dir"
        mkdir -p "$dir"
        echo "$content" > "$dir/__init__.py"
        echo "✅ Đã tạo $dir/__init__.py"
    fi
}

echo "🔍 Đảm bảo cấu trúc package Python hoạt động đúng..."

# Tạo hoặc cập nhật cấu trúc package
echo "📦 Đang tạo cấu trúc package Python..."

# Tạo các thư mục và file __init__.py với nội dung chính xác
SRC_DIR="$INSTALL_DIR/src"
COMMON_DIR="$SRC_DIR/common"
CONFIG_DIR="$COMMON_DIR/config"

# Đảm bảo các thư mục tồn tại
mkdir -p "$CONFIG_DIR"

# Tạo các file __init__.py
create_init_file "$SRC_DIR" '"""
WP Docker application.

This package is the main entry point for the WP Docker application,
providing functionality for managing WordPress websites with Docker.

The package is organized into the following modules:
- features: Domain-specific modules (website, backup, MySQL, etc.)
- common: Shared utilities and helper functions
- interfaces: Abstract base classes and interfaces
"""

__version__ = "2.0.0"'

create_init_file "$COMMON_DIR" '"""
Common utilities and shared functionality.

This package contains utilities and shared functionality used across
different modules of the WP Docker application.
"""'

create_init_file "$CONFIG_DIR" '"""
Module cấu hình hệ thống.

Module này cung cấp các lớp và công cụ cho việc quản lý cấu hình hệ thống.
"""

from src.common.config.manager import ConfigManager'

# Sao chép file manager.py từ thư mục gốc nếu cần
if [ ! -f "$CONFIG_DIR/manager.py" ]; then
    echo "🔄 Sao chép file manager.py từ thư mục gốc..."
    if [ -f "$ACTUAL_INSTALL_DIR/src/common/config/manager.py" ]; then
        cp "$ACTUAL_INSTALL_DIR/src/common/config/manager.py" "$CONFIG_DIR/"
        echo "✅ Đã sao chép manager.py"
    else
        echo "❌ Không tìm thấy file manager.py trong thư mục gốc."
        exit 1
    fi
fi

# Kiểm tra import để xác nhận
echo "🔍 Kiểm tra import src.common.config..."
if python3 -c "import sys; sys.path.insert(0, '$INSTALL_DIR'); import src.common.config" 2>/dev/null; then
    echo "✅ Import src.common.config thành công!"
else
    echo "❌ Vẫn không import được src.common.config. Cần kiểm tra thủ công."
fi

# Loại bỏ đường dẫn trùng lặp trong PYTHONPATH
clean_pythonpath() {
    local old_path="$1"
    local IFS=":"
    local result=""
    local seen=()
    
    for path in $old_path; do
        local found=0
        for seen_path in "${seen[@]}"; do
            if [ "$seen_path" = "$path" ]; then
                found=1
                break
            fi
        done
        
        if [ $found -eq 0 ]; then
            seen+=("$path")
            if [ -z "$result" ]; then
                result="$path"
            else
                result="$result:$path"
            fi
        fi
    done
    
    echo "$result"
}

# Thêm thư mục src vào PYTHONPATH và loại bỏ đường dẫn trùng lặp
export PYTHONPATH="$PYTHONPATH:$INSTALL_DIR/src:."
export PYTHONPATH=$(clean_pythonpath "$PYTHONPATH")
echo "📊 Đã cập nhật PYTHONPATH: $PYTHONPATH"

# Hiển thị thông tin môi trường để debug
echo "🔍 Thông tin môi trường Python:"
echo "Python path: $(which python3)"
echo "Virtual env Python: $PYTHON_EXEC"
echo "Virtualenv active: $VIRTUAL_ENV"

# Tạo file bootstrap tạm thời để khởi chạy ứng dụng
BOOTSTRAP_FILE="/tmp/wp_bootstrap_$$.py"
cat > "$BOOTSTRAP_FILE" << 'EOF'
#!/usr/bin/env python3
"""Bootstrap script to run main.py with proper module paths."""

import os
import sys
import importlib.util
import traceback

def add_to_path(path):
    """Add a path to sys.path if it's not already there."""
    if path not in sys.path:
        sys.path.insert(0, path)

def run_main(main_file):
    """Run the main program."""
    # Set sys.argv[0] to point to the main file
    sys.argv[0] = main_file
    
    print(f"🚀 Running main program: {main_file}")
    
    # Check if we can import src now
    try:
        import src
        print("✅ Import src successful")
        
        # Try more specific imports
        try:
            from src.common.config import manager
            print("✅ Import src.common.config.manager successful")
        except ImportError as e:
            print(f"❌ Import src.common.config.manager failed: {e}")
            print(f"   Looking for manager.py in: {os.path.dirname(src.common.config.__file__)}")
            # Manually create the module if needed
            if not hasattr(src.common.config, 'manager'):
                print("🔧 Manually creating ConfigManager module...")
                # Find the actual manager.py file
                for path in sys.path:
                    manager_path = os.path.join(path, "src", "common", "config", "manager.py")
                    if os.path.exists(manager_path):
                        print(f"📋 Found manager.py at: {manager_path}")
                        # Load the module manually
                        spec = importlib.util.spec_from_file_location("src.common.config.manager", manager_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules["src.common.config.manager"] = module
                        spec.loader.exec_module(module)
                        # Attach to parent module
                        src.common.config.manager = module
                        print("✅ Manually loaded manager.py")
                        break
    except ImportError as e:
        print(f"❌ Import src failed: {e}")
        print("⚠️ Check that __init__.py files exist in all directories")
        return 1

    # Execute the main program
    try:
        with open(main_file, 'r') as f:
            code = compile(f.read(), main_file, 'exec')
            exec(code, globals())
        return 0
    except Exception as e:
        print(f"❌ Error running main program: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Current directory should be the INSTALL_DIR
    install_dir = os.getcwd()
    
    # Add critical paths to sys.path
    add_to_path(install_dir)
    add_to_path(os.path.join(install_dir, 'src'))
    
    # Check paths
    print("Python sys.path (first 5 entries):")
    for p in sys.path[:5]:
        print(f"  - {p}")
    
    # Determine the main file path
    main_file = os.path.join(install_dir, "src", "main.py")
    
    # Run the main program
    sys.exit(run_main(main_file))
EOF

# Make it executable
chmod +x "$BOOTSTRAP_FILE"

# Chuyển đến thư mục cài đặt
cd "$INSTALL_DIR"

# Chạy bootstrap script
echo "🚀 Chạy bootstrap script để khởi động ứng dụng..."
"$PYTHON_EXEC" "$BOOTSTRAP_FILE"

# Dọn dẹp
rm -f "$BOOTSTRAP_FILE"