# File: core/backend/modules/backup/backup_restore.py

import os
import glob
import tarfile
import shutil
import subprocess
from datetime import datetime
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import get_sites_dir, get_site_config
from core.backend.modules.mysql.import_export import import_database
from core.backend.objects.container import Container

@log_call
def get_backup_folders(domain: str):
    """
    Get all backup folders for a domain.
    
    Args:
        domain: The domain name
        
    Returns:
        tuple: (backup_dir, backup_folders, last_backup_info)
    """
    sites_dir = get_sites_dir()
    backup_dir = os.path.join(sites_dir, domain, "backups")
    
    if not os.path.exists(backup_dir):
        error(f"❌ Không tìm thấy thư mục backup cho website {domain}.")
        return backup_dir, [], None
    
    # Tìm tất cả các thư mục backup trong thư mục backups
    backup_folders = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d)) and d.startswith("backup_")]
    
    if not backup_folders:
        error(f"❌ Không tìm thấy bản backup nào cho website {domain}.")
        return backup_dir, [], None
    
    # Lấy thông tin backup hiện tại nếu có
    site_config = get_site_config(domain)
    last_backup_info = None
    if site_config and site_config.backup and site_config.backup.last_backup:
        last_backup_info = site_config.backup.last_backup
        
    # Sắp xếp các thư mục backup theo thời gian tạo (mới nhất lên đầu)
    backup_folders = sorted(
        backup_folders,
        key=lambda x: os.path.getctime(os.path.join(backup_dir, x)),
        reverse=True
    )
    
    return backup_dir, backup_folders, last_backup_info

@log_call
def get_backup_info(backup_dir, folder, last_backup_info=None):
    """
    Get detailed information about a backup folder.
    
    Args:
        backup_dir: The backup directory
        folder: The backup folder name
        last_backup_info: The last backup info from config (optional)
        
    Returns:
        dict: Backup information
    """
    folder_path = os.path.join(backup_dir, folder)
    try:
        # Lấy thời gian tạo
        folder_time = datetime.fromtimestamp(os.path.getctime(folder_path))
        time_str = folder_time.strftime("%d/%m/%Y %H:%M:%S")
        
        # Tính kích thước tổng cộng
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        
        size_str = f"{total_size / (1024*1024):.2f} MB"
        
        # Kiểm tra xem đây có phải là backup gần nhất trong cấu hình không
        is_latest = False
        if last_backup_info and last_backup_info.file:
            if last_backup_info.file.startswith(folder_path):
                is_latest = True
        
        # Tìm kiếm các file trong thư mục backup
        archive_file = None
        sql_file = None
        
        for file_path in glob.glob(os.path.join(folder_path, "*.tar.gz")):
            archive_file = file_path
            break
        
        for file_path in glob.glob(os.path.join(folder_path, "*.sql")):
            sql_file = file_path
            break
            
        return {
            "folder": folder,
            "path": folder_path,
            "time": time_str,
            "timestamp": folder_time.timestamp(),
            "size": size_str,
            "size_bytes": total_size,
            "is_latest": is_latest,
            "archive_file": archive_file,
            "sql_file": sql_file
        }
    except Exception as e:
        warn(f"⚠️ Không thể lấy thông tin cho backup {folder}: {e}")
        return {
            "folder": folder,
            "path": folder_path,
            "error": str(e)
        }

@log_call
def restore_database(domain: str, sql_file: str, reset_db: bool = True):
    """
    Restore database from SQL file.
    
    Args:
        domain: The domain name
        sql_file: Path to the SQL file
        reset_db: Whether to reset the database before restoring
        
    Returns:
        bool: Success status
    """
    try:
        import_database(domain, sql_file, reset=reset_db)
        success(f"✅ Đã khôi phục database thành công.")
        return True
    except Exception as e:
        error(f"❌ Lỗi khi khôi phục database: {e}")
        return False

@log_call
def restore_source_code(domain: str, archive_file: str):
    """
    Restore source code from archive file.
    
    Args:
        domain: The domain name
        archive_file: Path to the archive file
        
    Returns:
        bool: Success status
    """
    sites_dir = get_sites_dir()
    wordpress_dir = os.path.join(sites_dir, domain, "wordpress")
    
    if not os.path.exists(wordpress_dir):
        error(f"❌ Không tìm thấy thư mục wordpress cho website {domain}.")
        return False
        
    try:
        # Tạo một thư mục tạm thời để giải nén
        temp_dir = os.path.join(sites_dir, domain, "temp_extract")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Giải nén file tar.gz
        with tarfile.open(archive_file, "r:gz") as tar:
            tar.extractall(path=temp_dir)
        
        # Di chuyển các file từ thư mục giải nén vào thư mục wordpress
        extracted_wordpress_dir = os.path.join(temp_dir, "wordpress")
        
        # Xóa thư mục wordpress hiện tại
        shutil.rmtree(wordpress_dir)
        
        # Di chuyển thư mục giải nén vào vị trí mới
        shutil.move(extracted_wordpress_dir, wordpress_dir)
        
        # Thiết lập quyền
        set_wordpress_permissions(domain)
        
        # Xóa thư mục tạm
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        success(f"✅ Đã khôi phục mã nguồn thành công.")
        return True
        
    except Exception as e:
        error(f"❌ Lỗi khi khôi phục mã nguồn: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

@log_call
def set_wordpress_permissions(domain: str):
    """
    Set proper permissions for WordPress files.
    
    Args:
        domain: The domain name
        
    Returns:
        bool: Success status
    """
    php_container_name = f"{domain}-php"
    php_container = Container(name=php_container_name)
    
    if not php_container.running():
        warn(f"⚠️ Container PHP ({php_container_name}) không hoạt động. Có thể cần phải khởi động lại website sau khi khôi phục.")
        return False
        
    try:
        php_container.exec(["chown", "-R", "www-data:www-data", "/var/www/html"], user="root")
        info("✅ Đã thiết lập quyền cho các file.")
        return True
    except Exception as e:
        warn(f"⚠️ Không thể thiết lập quyền: {e}")
        return False

@log_call
def restart_website(domain: str):
    """
    Restart website containers.
    
    Args:
        domain: The domain name
        
    Returns:
        bool: Success status
    """
    try:
        sites_dir = get_sites_dir()
        compose_dir = os.path.join(sites_dir, domain, "docker-compose")
        
        if os.path.exists(compose_dir):
            cmd = ["docker-compose", "-f", os.path.join(compose_dir, "docker-compose.yml"), "restart"]
            subprocess.run(cmd, check=True)
            success(f"✅ Đã khởi động lại website {domain} thành công.")
            return True
        else:
            warn(f"⚠️ Không tìm thấy thư mục docker-compose cho website {domain}.")
            return False
    except Exception as e:
        error(f"❌ Lỗi khi khởi động lại website: {e}")
        return False