# File: core/backend/modules/backup/website_backup.py

from core.backend.utils.debug import log_call, info, error
from core.backend.modules.website.website_utils import get_site_config
from core.backend.modules.backup.backup_actions import (
    backup_create_structure,
    backup_database,
    backup_files,
    backup_update_config,
    backup_finalize,
    rollback_backup
)

@log_call
def backup_website(domain: str):
    """
    Tiến hành backup toàn bộ website (code + database) theo từng bước có thể rollback nếu lỗi.
    """
    info(f"🚀 Bắt đầu backup website: {domain}")
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Không tìm thấy cấu hình website cho domain: {domain}")
        return

    try:
        # 1. Tạo thư mục backup
        backup_create_structure(domain)

        # 2. Backup database
        backup_database(domain)

        # 3. Backup mã nguồn (wp-content)
        backup_files(domain)
        
        # 4. Update configuration with backup information
        backup_update_config(domain)

        # 5. Ghi thông tin metadata hoặc hoàn tất
        backup_finalize(domain)

        info(f"✅ Hoàn tất backup website {domain}.")

    except Exception as e:
        error(f"❌ Backup thất bại: {e}")
        info("🔁 Đang rollback...")

        # Use the simplified rollback function with domain parameter
        rollback_backup(domain)

        error(f"❌ Đã rollback toàn bộ tiến trình backup cho {domain}.")
