print_msg() {
    local RED=$'\033[1;31m'
    local GREEN=$'\033[1;32m'
    local YELLOW=$'\033[1;33m'
    local BLUE=$'\033[1;36m'
    local MAGENTA=$'\033[1;35m'
    local CYAN=$'\033[1;36m'
    local WHITE=$'\033[1;37m'
    local STRONG=$'\033[1m'
    local NC=$'\033[0m'
    local type="$1"
    local message="$2"
    local color emoji

    case "$type" in
    success) emoji="✅" color="$GREEN" ;;
    error) emoji="❌" color="$RED" ;;
    warning) emoji="⚠️" color="$YELLOW" ;;
    info) emoji="ℹ️" color="$WHITE" ;;
    save) emoji="💾" color="$WHITE" ;;
    important) emoji="🚨" color="$RED" ;;
    step) emoji="➤" color="$MAGENTA" ;;
    check) emoji="🔍" color="$CYAN" ;;
    run) emoji="🚀" color="$GREEN" ;;
    skip) emoji="⏭️" color="$YELLOW" ;;
    cancel) emoji="🛑" color="$RED" ;;
    question) emoji="❓" color="$WHITE" ;;
    completed) emoji="🏁" color="$GREEN" ;;
    recommend) emoji="💡" color="$BLUE" ;;
    title) emoji="📌" color="$CYAN" ;;
    label) emoji="" color="$BLUE" ;;
    sub_label) emoji="➥" color="$WHITE" ;;

    *)
        echo -e "$message"
        return
        ;;
    esac

    echo -e "${color}${emoji} ${message}${NC}"
}
