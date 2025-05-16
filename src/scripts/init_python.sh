init_python_env() {
    # Tạo virtualenv nếu chưa có
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "📦 Creating Python virtual environment..."
        
        # Try standard venv creation first
        if ! python3 -m venv "$VENV_DIR" 2>/tmp/venv_error.log; then
            echo "⚠️ Standard venv creation failed. Using fallback method..."
            
            # Check if the fallback helper script exists
            HELPER_SCRIPT="$(dirname "$0")/helpers/create_venv.py"
            if [ -f "$HELPER_SCRIPT" ] && [ -x "$HELPER_SCRIPT" ]; then
                echo "🔧 Using helper script to create virtualenv..."
                python3 "$HELPER_SCRIPT" "$VENV_DIR"
            else
                echo "❌ Error: Unable to create virtual environment. Please check Python installation."
                echo "Error details:"
                cat /tmp/venv_error.log
                exit 1
            fi
        fi
        
        # Verify the virtualenv was created successfully
        if [ ! -f "$VENV_DIR/bin/activate" ]; then
            echo "❌ Error: Virtual environment created but activate script is missing."
            echo "Please check Python installation and try again."
            exit 1
        fi
    fi

    # Kích hoạt virtualenv và cài thư viện cần thiết
    echo "🐍 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    export PYTHONPATH="$INSTALL_DIR"

    if [[ ! -f "$VENV_DIR/.installed" && -f "$INSTALL_DIR/requirements.txt" ]]; then
        echo "📦 Installing Python dependencies..."
        pip install --upgrade pip
        pip install -r "$INSTALL_DIR/requirements.txt"
        touch "$VENV_DIR/.installed"
    else
        echo "✅ Python dependencies already installed."
    fi
}
