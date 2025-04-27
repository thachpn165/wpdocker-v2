#!/bin/bash

# Wrapper để chạy bất kỳ file Python trong container runtime
# Ví dụ: ./scripts/run.py.sh core/backend/menu_main.py

PYTHON_CONTAINER="wpdocker-python-runtime"
PYTHON_PATH="/app"

if [[ $# -eq 0 ]]; then
    echo "❌ Vui lòng truyền tên file .py cần chạy, ví dụ:"
    echo "   ./scripts/run.py.sh core/backend/menu_main.py"
    exit 1
fi

docker exec -it "$PYTHON_CONTAINER" python3 "$PYTHON_PATH/$1"
