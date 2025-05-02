from questionary import select, confirm
import os
from core.backend.utils.debug import log_call, info, warn, error, success, debug
from core.backend.modules.website.website_utils import select_website
from core.backend.modules.mysql.import_export import import_database
from core.backend.utils.env_utils import env


@log_call
def prompt_restore_database():
    try:
        # Chọn website để khôi phục
        domain = select_website("🌐 Chọn website để khôi phục database:")
        if not domain:
            info("Đã huỷ thao tác.")
            return

        # Hỏi có muốn xoá dữ liệu hiện tại không
        reset = confirm(
            "🗑️ Bạn có muốn xoá dữ liệu hiện tại trước khi khôi phục không?"
        ).ask()

        # Hướng dẫn chuẩn bị file backup
        backup_path = os.path.join(
            env.get("SITSE_DIR", "/opt/wp-docker/data/sites"), domain, "backups"
        )
        info(
            f"📁 Vui lòng đảm bảo file SQL đã được đặt trong thư mục: {backup_path}"
        )

        # Kiểm tra thư mục backup đã tồn tại chưa
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)
            success(f"✅ Đã tạo thư mục backup tại: {backup_path}")

        # Xác nhận đã chuẩn bị file
        if not confirm("❓ Bạn đã đặt file SQL vào thư mục backup chưa?").ask():
            info("Đã huỷ thao tác. Hãy chuẩn bị file backup trước.")
            return

        # Lấy danh sách các file trong thư mục backup
        backup_files = [f for f in os.listdir(backup_path) if f.endswith('.sql')]

        if not backup_files:
            error("❌ Không tìm thấy file SQL nào trong thư mục backup.")
            return

        # Chọn file để khôi phục
        selected_file = select(
            "📦 Chọn file SQL để khôi phục:",
            choices=backup_files
        ).ask()

        if not selected_file:
            info("Đã huỷ thao tác.")
            return

        # Đường dẫn đầy đủ đến file backup
        db_file = os.path.join(backup_path, selected_file)

        # Khôi phục database
        if confirm(f"⚠️ Xác nhận khôi phục database cho {domain} từ file {selected_file}?").ask():
            import_database(domain, db_file, reset)
            success(f"✅ Đã hoàn thành khôi phục database cho website {domain}.")
        else:
            info("Đã huỷ thao tác khôi phục.")

    except (KeyboardInterrupt, EOFError):
        print("\nĐã huỷ thao tác.")
        return
