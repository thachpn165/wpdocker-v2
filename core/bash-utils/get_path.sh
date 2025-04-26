#!/bin/bash
# =============================================
# 📁 Định nghĩa các đường dẫn quan trọng theo INSTALL_DIR
# =============================================

get_path_core() {
    echo "$INSTALL_DIR/core"
}

get_path_data() {
    echo "$INSTALL_DIR/data"
}

get_path_config() {
    echo "$INSTALL_DIR/config"
}

get_path_templates() {
    echo "$INSTALL_DIR/core/templates"
}

get_path_docker_compose() {
    echo "$INSTALL_DIR/docker-compose"
}

get_path_docker_compose_runtime() {
    echo "$INSTALL_DIR/docker-compose/docker-compose.runtime.yml"
}

get_path_site_dir() {
    local domain="$1"
    echo "$INSTALL_DIR/data/website/$domain"
}

get_path_site_logs() {
    local domain="$1"
    echo "$(get_path_site_dir "$domain")/logs"
}

get_path_site_php() {
    local domain="$1"
    echo "$(get_path_site_dir "$domain")/php"
}
