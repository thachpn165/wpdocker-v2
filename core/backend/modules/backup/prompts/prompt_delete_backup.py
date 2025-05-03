from questionary import select, confirm, checkbox
import os
import glob
import shutil
from datetime import datetime
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import website_list, get_sites_dir
from core.backend.modules.website.website_utils import get_site_config, set_site_config, delete_site_config
from core.backend.models.config import SiteBackup, SiteBackupInfo

@log_call
def prompt_delete_backup():
    """
    Hiển thị prompt để người dùng chọn và xóa backup của website.
    """
    # Lấy danh sách website
    websites = website_list()
    if not websites:
        error("❌ Không tìm thấy website nào để xóa backup.")
        return
    
    # Chọn một website
    domain = select(
        "🌐 Chọn website để xóa backup:",
        choices=websites
    ).ask()
    
    if not domain:
        info("Đã huỷ thao tác xóa backup.")
        return
    
    # Lấy thư mục backups của website
    sites_dir = get_sites_dir()
    backup_dir = os.path.join(sites_dir, domain, "backups")
    
    if not os.path.exists(backup_dir):
        error(f"❌ Không tìm thấy thư mục backup cho website {domain}.")
        return
    
    # Tìm tất cả các thư mục backup trong thư mục backups
    backup_folders = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d)) and d.startswith("backup_")]
    
    if not backup_folders:
        error(f"❌ Không tìm thấy bản backup nào cho website {domain}.")
        return
    
    # Tạo danh sách hiển thị với thông tin thêm về thời gian
    display_choices = []
    for folder in backup_folders:
        folder_path = os.path.join(backup_dir, folder)
        try:
            # Lấy thời gian tạo thư mục
            folder_time = datetime.fromtimestamp(os.path.getctime(folder_path))
            time_str = folder_time.strftime("%d/%m/%Y %H:%M:%S")
            
            # Tính kích thước của thư mục
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            
            size_str = f"{total_size / (1024*1024):.2f} MB"
            
            display_choices.append(f"{folder} ({time_str}, {size_str})")
        except Exception as e:
            display_choices.append(f"{folder} (Không thể lấy thông tin: {e})")
    
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
            # Lấy tên thư mục từ lựa chọn được hiển thị
            folder_name = selected_backup.split(" ")[0]
            folder_path = os.path.join(backup_dir, folder_name)
            
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
                    folder_path = os.path.join(backup_dir, folder)
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
            for folder in backup_folders:
                folder_path = os.path.join(backup_dir, folder)
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