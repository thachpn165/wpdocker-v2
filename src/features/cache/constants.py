# src/features/cache/constants.py

# Danh sách loại cache hỗ trợ
CACHE_TYPES = [
    "fastcgi-cache",
    "wp-super-cache",
    "w3-total-cache",
    "wp-fastest-cache",
    "no-cache"
]

# Map loại cache <-> plugin cần thiết (nếu có)
CACHE_PLUGINS = {
    "fastcgi-cache": ["redis-cache", "nginx-helper"],
    "wp-super-cache": ["wp-super-cache"],
    "w3-total-cache": ["w3-total-cache"],
    "wp-fastest-cache": ["wp-fastest-cache"],
    "no-cache": []
}

# Map loại cache <-> thông báo hướng dẫn sau khi cài đặt
CACHE_SETUP_NOTICE = {
    "fastcgi-cache": (
        "✅ FastCGI cache đã được thiết lập thành công cho {domain}!\n\n"
        "👉 Để tối ưu xóa cache tự động, hãy truy cập WP-Admin > Settings > NGINX Helper và bật tính năng Purge cache.\n"
        "- Đảm bảo plugin NGINX Helper đã được kích hoạt.\n"
        "- Bạn có thể xóa cache thủ công qua menu NGINX Helper hoặc truy cập /purge/URL.\n"
    ),
    "wp-super-cache": (
        "✅ WP Super Cache đã được thiết lập cho {domain}!\n\n"
        "👉 Vào WP-Admin > Settings > WP Super Cache để bật chế độ Caching On và cấu hình các tuỳ chọn phù hợp.\n"
    ),
    "w3-total-cache": (
        "✅ W3 Total Cache đã được thiết lập cho {domain}!\n\n"
        "👉 Vào WP-Admin > Performance để bật Page Cache, Browser Cache và các tuỳ chọn khác.\n"
    ),
    "wp-fastest-cache": (
        "✅ WP Fastest Cache đã được thiết lập cho {domain}!\n\n"
        "👉 Vào WP-Admin > WP Fastest Cache để bật Cache System, Preload, Minify HTML/CSS, v.v.\n"
    ),
    "no-cache": (
        "⚠️ Đã tắt toàn bộ cache cho {domain}. Website sẽ không sử dụng bất kỳ cơ chế cache nào.\n"
    ),
} 