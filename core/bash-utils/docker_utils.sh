# ==============================
# Tạo network cho Docker từ DOCKER_NETWORK
# ==============================
docker_create_network() {
    local network_name="$1"

    if ! docker network ls --format '{{.Name}}' | grep -q "^$network_name$"; then
        print_msg info "Creating Docker network: $network_name"
        docker network create "$network_name"
        if [[ $? -eq 0 ]]; then
            print_msg success "Docker network $network_name created successfully"
        else
            print_msg error "Failed to create Docker network $network_name"
            return 1
        fi
    else
        print_msg info "Docker network $network_name already exists"
    fi
}