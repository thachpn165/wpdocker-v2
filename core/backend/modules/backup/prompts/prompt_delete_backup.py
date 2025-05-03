from questionary import select, confirm, checkbox
import os
import shutil
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import select_website, get_site_config, set_site_config
from core.backend.modules.backup.backup_restore import get_backup_folders, get_backup_info

@log_call
def prompt_delete_backup():
    """
    Hiển thị prompt để người dùng chọn và xóa backup của website.
    """
    # Chọn một website sử dụng hàm select_website có sẵn
    domain = select_website("🌐 Chọn website để xóa backup:")
    
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
    
    # Hỏi người dùng muốn xóa một hay nhiều backup
    delete_mode = select(
        "🔍 Bạn muốn xóa backup như thế nào?",
        choices=[
            "Xóa một bản backup",
            "Xóa nhiều bản backup",
            "Xóa tất cả bản backup"
        ]
    ).ask()
    
    if delete_mode == "Xóa một bản backup":
        # Chọn một backup để xóa
        selected_backup = select(
            "📁 Chọn bản backup để xóa:",
            choices=display_choices
        ).ask()
        
        if selected_backup:
            # Lấy thông tin backup đã chọn
            folder_name = selected_backup.split(" ")[0]
            selected_index = next((i for i, item in enumerate(backup_info_list) if item["folder"] == folder_name), -1)
            
            if selected_index == -1:
                error(f"❌ Không tìm thấy thông tin cho bản backup đã chọn.")
                return
                
            backup_info = backup_info_list[selected_index]
            folder_path = backup_info["path"]
            
            if confirm(f"⚠️ Xác nhận xóa backup {folder_name} của website {domain}?").ask():
                try:
                    shutil.rmtree(folder_path)
                    success(f"✅ Đã xóa backup {folder_name} của website {domain}.")
                    
                    # Kiểm tra nếu backup này được lưu trong cấu hình
                    _cleanup_backup_config(domain, folder_path)
                except Exception as e:
                    error(f"❌ Lỗi khi xóa backup {folder_name}: {e}")
            else:
                info("Đã huỷ thao tác xóa backup.")
    
    elif delete_mode == "Xóa nhiều bản backup":
        # Chọn nhiều backup để xóa
        backup_indices = [i for i in range(len(display_choices))]
        backup_choices = [f"{i+1}. {choice}" for i, choice in zip(backup_indices, display_choices)]
        
        selected_backups = checkbox(
            "📁 Chọn các bản backup để xóa (dùng phím space để chọn):",
            choices=backup_choices
        ).ask()
        
        if selected_backups:
            # Lấy danh sách các index được chọn
            selected_indices = [int(item.split(".")[0]) - 1 for item in selected_backups]
            selected_folders = [backup_folders[i] for i in selected_indices]
            
            if confirm(f"⚠️ Xác nhận xóa {len(selected_folders)} bản backup của website {domain}?").ask():
                for folder in selected_folders:
                    folder_info = next((info for info in backup_info_list if info["folder"] == folder), None)
                    if folder_info:
                        folder_path = folder_info["path"]
                        try:
                            shutil.rmtree(folder_path)
                            success(f"✅ Đã xóa backup {folder} của website {domain}.")
                            
                            # Kiểm tra nếu backup này được lưu trong cấu hình
                            _cleanup_backup_config(domain, folder_path)
                        except Exception as e:
                            error(f"❌ Lỗi khi xóa backup {folder}: {e}")
                
                info(f"🎉 Đã hoàn tất xóa {len(selected_folders)} bản backup.")
            else:
                info("Đã huỷ thao tác xóa backup.")
    
    elif delete_mode == "Xóa tất cả bản backup":
        if confirm(f"⚠️ CẢNH BÁO: Xác nhận xóa TẤT CẢ {len(backup_folders)} bản backup của website {domain}?").ask():
            for backup_info in backup_info_list:
                folder = backup_info["folder"]
                folder_path = backup_info["path"]
                try:
                    shutil.rmtree(folder_path)
                    success(f"✅ Đã xóa backup {folder} của website {domain}.")
                except Exception as e:
                    error(f"❌ Lỗi khi xóa backup {folder}: {e}")
            
            # Xóa toàn bộ cấu hình backup
            site_config = get_site_config(domain)
            if site_config and site_config.backup:
                site_config.backup = None
                set_site_config(domain, site_config)
                info(f"🧹 Đã xóa thông tin backup trong cấu hình cho {domain}")
            
            info(f"🎉 Đã hoàn tất xóa tất cả bản backup của website {domain}.")
        else:
            info("Đã huỷ thao tác xóa backup.")

def _cleanup_backup_config(domain, deleted_folder_path):
    """Helper function to clean up backup config if needed."""
    site_config = get_site_config(domain)
    if not site_config or not site_config.backup or not site_config.backup.last_backup:
        return
    
    backup_info = site_config.backup.last_backup
    
    # Kiểm tra nếu file trong cấu hình thuộc thư mục đã xóa
    if backup_info.file and backup_info.file.startswith(deleted_folder_path):
        info(f"🔍 Phát hiện cấu hình backup đang trỏ đến file đã xóa")
        
        # Xóa thông tin backup
        site_config.backup = None
        set_site_config(domain, site_config)
        info(f"🧹 Đã xóa thông tin backup trong cấu hình cho {domain}")