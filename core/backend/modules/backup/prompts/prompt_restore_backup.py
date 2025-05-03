from questionary import select, confirm, checkbox
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import select_website
from core.backend.modules.backup.backup_restore import (
    get_backup_folders,
    get_backup_info,
    restore_database,
    restore_source_code,
    restart_website
)
import os

@log_call
def prompt_restore_backup():
    """
    Hiển thị prompt để người dùng chọn và khôi phục backup của website.
    """
    # Chọn một website sử dụng hàm select_website có sẵn
    domain = select_website("🌐 Chọn website để khôi phục backup:")
    
    if not domain:
        # Thông báo lỗi đã được hiển thị trong hàm select_website
        return
    
    # Lấy thông tin về các thư mục backup
    backup_dir, backup_folders, last_backup_info = get_backup_folders(domain)
    
    if not backup_folders:
        return  # Thông báo lỗi đã được hiển thị trong hàm get_backup_folders
    
    # Tạo danh sách hiển thị với thông tin thêm về thời gian và kích thước
    display_choices = []
    backup_info_list = []
    
    for folder in backup_folders:
        backup_info = get_backup_info(backup_dir, folder, last_backup_info)
        backup_info_list.append(backup_info)
        
        if "error" in backup_info:
            display_choices.append(f"{folder} (Không thể lấy thông tin: {backup_info['error']})")
        else:
            status = "✅ Là bản backup gần nhất" if backup_info["is_latest"] else ""
            display_choices.append(f"{folder} [{backup_info['time']}] [{backup_info['size']}] {status}")
    
    # Chọn một backup để khôi phục
    selected_backup = select(
        "📁 Chọn bản backup để khôi phục:",
        choices=display_choices
    ).ask()
    
    if not selected_backup:
        info("Đã huỷ thao tác khôi phục backup.")
        return
    
    # Lấy thông tin backup đã chọn
    folder_name = selected_backup.split(" ")[0]
    selected_index = next((i for i, item in enumerate(backup_info_list) if item["folder"] == folder_name), -1)
    
    if selected_index == -1:
        error(f"❌ Không tìm thấy thông tin cho bản backup đã chọn.")
        return
        
    backup_info = backup_info_list[selected_index]
    info(f"📂 Bạn đã chọn bản backup: {folder_name}")
    
    # Kiểm tra xem có file cần thiết không
    if not backup_info.get("archive_file") and not backup_info.get("sql_file"):
        error(f"❌ Không tìm thấy file backup (tar.gz hoặc sql) trong thư mục {folder_name}.")
        return
    
    # Cho người dùng chọn các thành phần để khôi phục
    components = []
    
    if backup_info.get("archive_file"):
        components.append("Mã nguồn website")
    
    if backup_info.get("sql_file"):
        components.append("Database")
    
    if not components:
        error("❌ Không có thành phần nào để khôi phục.")
        return
    
    selected_components = checkbox(
        "🔄 Chọn các thành phần để khôi phục (dùng phím space để chọn):",
        choices=components
    ).ask()
    
    if not selected_components:
        info("Đã huỷ thao tác khôi phục backup.")
        return
    
    # Xác nhận khôi phục
    if not confirm(f"⚠️ CẢNH BÁO: Khôi phục sẽ ghi đè lên dữ liệu hiện tại của website {domain}. Bạn có chắc chắn muốn tiếp tục?").ask():
        info("Đã huỷ thao tác khôi phục backup.")
        return
    
    # Tiến hành khôi phục
    info(f"🔄 Bắt đầu quá trình khôi phục backup cho website {domain}...")
    restore_success = True
    
    # Khôi phục database
    if "Database" in selected_components and backup_info.get("sql_file"):
        sql_file = backup_info["sql_file"]
        info(f"💾 Khôi phục database từ file: {os.path.basename(sql_file)}")
        
        # Hỏi người dùng có muốn xóa database hiện tại không
        reset_db = confirm("🗑️ Bạn có muốn xóa dữ liệu database hiện tại trước khi khôi phục?").ask()
        
        if not restore_database(domain, sql_file, reset_db):
            restore_success = False
    
    # Khôi phục mã nguồn
    if "Mã nguồn website" in selected_components and backup_info.get("archive_file"):
        archive_file = backup_info["archive_file"]
        info(f"📦 Khôi phục mã nguồn từ file: {os.path.basename(archive_file)}")
        
        # Hỏi người dùng xác nhận
        if confirm(f"⚠️ Quá trình này sẽ GHI ĐÈ lên tất cả file trong thư mục wordpress của {domain}. Tiếp tục?").ask():
            if not restore_source_code(domain, archive_file):
                restore_success = False
        else:
            info("Đã huỷ thao tác khôi phục mã nguồn.")
    
    # Hỏi người dùng có muốn khởi động lại website không
    if restore_success:
        if confirm(f"🔄 Bạn có muốn khởi động lại website {domain} không?").ask():
            restart_website(domain)
        
        success(f"🎉 Đã hoàn tất khôi phục backup cho website {domain}.")
    else:
        error(f"❌ Quá trình khôi phục backup gặp một số lỗi. Vui lòng kiểm tra lại website {domain}.")