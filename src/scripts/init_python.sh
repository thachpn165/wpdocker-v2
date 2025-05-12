init_python_env() {
    # Tạo virtualenv nếu chưa có
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "📦 Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
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
