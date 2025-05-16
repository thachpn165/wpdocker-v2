#!/bin/bash
# Script kiểm tra môi trường ảo Python
# Sử dụng: ./check_venv.sh

# Định nghĩa hàm in màu sắc
print_color() {
    local color="$1"
    local message="$2"
    
    # ANSI color codes
    local reset='\033[0m'
    local red='\033[0;31m'
    local green='\033[0;32m'
    local yellow='\033[0;33m'
    local blue='\033[0;34m'
    
    case "$color" in
        "red") echo -e "${red}${message}${reset}" ;;
        "green") echo -e "${green}${message}${reset}" ;;
        "yellow") echo -e "${yellow}${message}${reset}" ;;
        "blue") echo -e "${blue}${message}${reset}" ;;
        *) echo "$message" ;;
    esac
}

echo_step() {
    print_color "blue" "🔹 $1"
}

echo_success() {
    print_color "green" "✅ $1"
}

echo_error() {
    print_color "red" "❌ $1"
}

echo_warning() {
    print_color "yellow" "⚠️ $1"
}

echo_info() {
    print_color "blue" "ℹ️ $1"
}

# Đường dẫn cố định cho thư mục cài đặt
FIXED_INSTALL_DIR="/opt/wp-docker"

# Đường dẫn thực tế (sẽ được sử dụng nếu đường dẫn cố định không tồn tại)
ACTUAL_INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Sử dụng đường dẫn cố định nếu có, nếu không sử dụng đường dẫn thực tế
if [ -d "$FIXED_INSTALL_DIR" ] || [ -L "$FIXED_INSTALL_DIR" ]; then
    INSTALL_DIR="$FIXED_INSTALL_DIR"
    echo_info "Sử dụng đường dẫn cố định: $INSTALL_DIR"
else
    INSTALL_DIR="$ACTUAL_INSTALL_DIR"
    echo_info "Sử dụng đường dẫn thực tế: $INSTALL_DIR"
fi

VENV_DIR="$INSTALL_DIR/.venv"

# Header
echo "=========================="
print_color "blue" "🔍 KIỂM TRA MÔI TRƯỜNG ẢO PYTHON"
echo "=========================="
echo

# Kiểm tra Python hệ thống
echo_step "Kiểm tra Python hệ thống"
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo_success "Python đã được cài đặt: $PYTHON_VERSION"
else
    echo_error "Không tìm thấy Python trong hệ thống"
    exit 1
fi

# Kiểm tra thư mục virtualenv
echo_step "Kiểm tra thư mục môi trường ảo"
if [ -d "$VENV_DIR" ]; then
    echo_success "Thư mục môi trường ảo tồn tại: $VENV_DIR"
    
    # Kiểm tra cấu trúc thư mục
    if [ -d "$VENV_DIR/bin" ]; then
        echo_success "Cấu trúc thư mục bin tồn tại"
    else
        echo_error "Không tìm thấy thư mục bin trong môi trường ảo"
    fi
    
    # Kiểm tra tệp activate
    if [ -f "$VENV_DIR/bin/activate" ]; then
        echo_success "Tệp activate tồn tại"
    else
        echo_error "Không tìm thấy tệp activate"
    fi
    
    # Kiểm tra tệp python
    if [ -f "$VENV_DIR/bin/python" ]; then
        echo_success "Tệp python tồn tại"
        VENV_PYTHON_VERSION=$("$VENV_DIR/bin/python" --version 2>&1)
        echo_info "Phiên bản Python trong môi trường ảo: $VENV_PYTHON_VERSION"
    else
        echo_error "Không tìm thấy tệp python trong môi trường ảo"
    fi
    
    # Kiểm tra tệp pip
    if [ -f "$VENV_DIR/bin/pip" ]; then
        echo_success "Tệp pip tồn tại"
        VENV_PIP_VERSION=$("$VENV_DIR/bin/pip" --version 2>&1)
        echo_info "Phiên bản pip trong môi trường ảo: $VENV_PIP_VERSION"
    else
        echo_error "Không tìm thấy tệp pip trong môi trường ảo"
    fi
else
    echo_error "Thư mục môi trường ảo không tồn tại: $VENV_DIR"
fi

# Kích hoạt môi trường ảo và kiểm tra
echo_step "Kích hoạt và kiểm tra môi trường ảo"
if [ -f "$VENV_DIR/bin/activate" ]; then
    # Lưu đường dẫn Python hiện tại
    CURRENT_PYTHON_PATH=$(which python3)
    
    # Kích hoạt môi trường ảo
    echo_info "Kích hoạt môi trường ảo..."
    source "$VENV_DIR/bin/activate"
    
    # Kiểm tra đường dẫn Python sau khi kích hoạt
    VENV_PYTHON_PATH=$(which python)
    if [[ "$VENV_PYTHON_PATH" == *"$VENV_DIR"* ]]; then
        echo_success "Môi trường ảo đã được kích hoạt thành công"
        echo_info "Python path trước khi kích hoạt: $CURRENT_PYTHON_PATH"
        echo_info "Python path sau khi kích hoạt: $VENV_PYTHON_PATH"
    else
        echo_error "Kích hoạt môi trường ảo không thành công"
        echo_info "Python path vẫn là: $VENV_PYTHON_PATH"
    fi
    
    # Kiểm tra biến môi trường VIRTUAL_ENV
    if [ -n "$VIRTUAL_ENV" ]; then
        echo_success "Biến môi trường VIRTUAL_ENV đã được thiết lập: $VIRTUAL_ENV"
    else
        echo_error "Biến môi trường VIRTUAL_ENV không được thiết lập"
    fi
    
    # Thử import một số module cơ bản
    echo_info "Kiểm tra import modules..."
    if python -c "import sys; print('Python path:', sys.path)" &>/dev/null; then
        echo_success "Import sys thành công"
    else
        echo_error "Import sys thất bại"
    fi
    
    # Hủy kích hoạt môi trường ảo
    deactivate 2>/dev/null || true
else
    echo_error "Không thể kích hoạt môi trường ảo vì tệp activate không tồn tại"
fi

# Thử chạy ứng dụng với Python trong môi trường ảo để kiểm tra
echo_step "Kiểm tra khả năng chạy ứng dụng với Python trong môi trường ảo"
if [ -f "$VENV_DIR/bin/python" ] && [ -f "$INSTALL_DIR/src/main.py" ]; then
    echo_info "Thử import module từ ứng dụng..."
    
    # Kiểm tra import src và src.common
    cd "$INSTALL_DIR"
    echo_info "Thư mục hiện tại: $(pwd)"
    
    # Đặt PYTHONPATH
    export PYTHONPATH="$INSTALL_DIR"
    echo_info "PYTHONPATH: $PYTHONPATH"
    
    # Thử import src module (không thực sự chạy ứng dụng)
    if "$VENV_DIR/bin/python" -c "import sys; print('Python path:', sys.path[:3])" 2>/dev/null; then
        echo_success "Python path import thành công"
    else
        echo_error "Python path import thất bại"
    fi
    
    if "$VENV_DIR/bin/python" -c "import src; print('Imported src module successfully')" 2>/dev/null; then
        echo_success "Import src module thành công"
    else
        echo_error "Import src module thất bại"
        ERROR_OUTPUT=$("$VENV_DIR/bin/python" -c "import src" 2>&1)
        echo_info "Lỗi: $ERROR_OUTPUT"
    fi
    
    # Thử cách khác với thư mục src trong path
    echo_info "Thử với PYTHONPATH bao gồm cả thư mục src..."
    export PYTHONPATH="$INSTALL_DIR:$INSTALL_DIR/src"
    
    if "$VENV_DIR/bin/python" -c "import src; print('Imported src module successfully')" 2>/dev/null; then
        echo_success "Import src module thành công với PYTHONPATH mở rộng"
    else
        echo_error "Import src module thất bại với PYTHONPATH mở rộng"
    fi
    
    # Reset PYTHONPATH
    unset PYTHONPATH
else
    echo_error "Không thể kiểm tra khả năng chạy ứng dụng (thiếu Python trong virtualenv hoặc file main.py)"
fi

# Tổng kết
echo 
echo "=========================="
print_color "blue" "🔍 KẾT QUẢ KIỂM TRA"
echo "=========================="

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ] && [ -f "$VENV_DIR/bin/python" ]; then
    echo_success "Môi trường ảo tồn tại và có vẻ hoạt động bình thường"
    echo_info "Nếu vẫn gặp vấn đề khi chạy ứng dụng, hãy thử các bước sau:"
    echo_info "1. Xóa thư mục môi trường ảo: rm -rf $VENV_DIR"
    echo_info "2. Chạy lại script init.sh để tạo môi trường ảo mới"
    echo_info "3. Đảm bảo PYTHONPATH chỉ đến thư mục gốc của dự án"
else
    echo_error "Môi trường ảo không hoạt động bình thường"
    echo_info "Hãy thử các bước sau:"
    echo_info "1. Xóa thư mục môi trường ảo: rm -rf $VENV_DIR"
    echo_info "2. Cài đặt lại gói python3-venv: sudo apt install python3-venv python3-dev"
    echo_info "3. Chạy lại script init.sh để tạo môi trường ảo mới"
fi