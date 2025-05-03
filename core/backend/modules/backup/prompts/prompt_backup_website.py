from questionary import select, confirm, checkbox
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import website_list
from core.backend.modules.backup.website_backup import backup_website

@log_call
def prompt_backup_website():
    """
    Hiển thị prompt để người dùng chọn website cần backup.
    Cho phép chọn một hoặc nhiều website để backup.
    """
    # Lấy danh sách website
    websites = website_list()
    if not websites:
        error("❌ Không tìm thấy website nào để backup.")
        return
    
    # Hỏi người dùng muốn backup một hay nhiều website
    backup_mode = select(
        "🔍 Bạn muốn backup website như thế nào?",
        choices=[
            "Backup một website",
            "Backup nhiều website"
        ]
    ).ask()
    
    if backup_mode == "Backup một website":
        # Chọn một website
        domain = select(
            "🌐 Chọn website cần backup:",
            choices=websites
        ).ask()
        
        if domain:
            if confirm(f"⚠️ Xác nhận backup website {domain}?").ask():
                info(f"⏳ Đang tiến hành backup website {domain}...")
                backup_website(domain)
            else:
                info("Đã huỷ thao tác backup.")
    else:
        # Chọn nhiều website
        selected_domains = checkbox(
            "🌐 Chọn các website cần backup (dùng phím space để chọn):",
            choices=websites
        ).ask()
        
        if selected_domains:
            if confirm(f"⚠️ Xác nhận backup {len(selected_domains)} website?").ask():
                for domain in selected_domains:
                    info(f"⏳ Đang tiến hành backup website {domain}...")
                    try:
                        backup_website(domain)
                        success(f"✅ Backup website {domain} hoàn tất.")
                    except Exception as e:
                        error(f"❌ Lỗi khi backup website {domain}: {e}")
                
                info(f"🎉 Đã hoàn tất backup {len(selected_domains)} website.")
            else:
                info("Đã huỷ thao tác backup.")
        else:
            info("Không có website nào được chọn để backup.")