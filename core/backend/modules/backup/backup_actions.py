# File: core/backend/modules/backup/backup_actions.py

import os
import shutil
import glob
from datetime import datetime
from core.backend.utils.env_utils import env_required, env
from core.backend.modules.website.website_utils import get_site_config, set_site_config, delete_site_config
from core.backend.modules.mysql.import_export import export_database
from core.backend.utils.debug import log_call, info, error, warn, debug
from core.backend.modules.website.website_utils import get_sites_dir
from core.backend.models.config import SiteBackup, SiteBackupInfo
import tarfile

BACKUP_TEMP_STATE = {}


@log_call
def backup_create_structure(domain: str):
    sites_dir = get_sites_dir()
    debug(f"Sites dir: {sites_dir}")
    base_dir = os.path.join(sites_dir, domain, "backups")
    os.makedirs(base_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(base_dir, f"backup_{timestamp}")
    os.makedirs(backup_path)

    BACKUP_TEMP_STATE["backup_path"] = backup_path
    info(f"📁 Thư mục backup đã tạo: {backup_path}")

@log_call
def backup_database(domain: str):
    if "backup_path" not in BACKUP_TEMP_STATE:
        raise RuntimeError("❌ backup_path chưa được khởi tạo.")

    target = BACKUP_TEMP_STATE["backup_path"]
    export_database(domain, target)
    info("💾 Đã backup database thành công.")

@log_call
def backup_files(domain: str):
    if "backup_path" not in BACKUP_TEMP_STATE:
        raise RuntimeError("❌ backup_path chưa được khởi tạo.")

    sites_dir = get_sites_dir()
    site_dir = os.path.join(sites_dir, domain, "wordpress")
    
    # Create a tar.gz archive instead of copying files
    backup_path = BACKUP_TEMP_STATE["backup_path"]
    archive_filename = os.path.join(backup_path, "wordpress.tar.gz")
    
    # Create the archive
    with tarfile.open(archive_filename, "w:gz") as tar:
        # Add the wordpress directory to the archive
        tar.add(site_dir, arcname="wordpress")
    
    # Store the archive path in the state
    BACKUP_TEMP_STATE["wordpress_archive"] = archive_filename
    
    info(f"📦 Đã tạo file nén mã nguồn website: {archive_filename}")
    debug(f"Kích thước file: {os.path.getsize(archive_filename) / (1024*1024):.2f} MB")

@log_call
def backup_update_config(domain: str):
    """Update the site configuration with backup information."""
    if "backup_path" not in BACKUP_TEMP_STATE:
        raise RuntimeError("❌ backup_path chưa được khởi tạo.")
    
    backup_path = BACKUP_TEMP_STATE.get("backup_path")
    wordpress_archive = BACKUP_TEMP_STATE.get("wordpress_archive", "")
    
    # Find the most recent SQL file in the backup directory
    sql_files = glob.glob(os.path.join(backup_path, "*.sql"))
    database_file = ""
    if sql_files:
        # Sort by modification time, newest first
        database_file = sorted(sql_files, key=os.path.getmtime, reverse=True)[0]
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get the site configuration
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Không tìm thấy cấu hình cho website: {domain}")
        return False
    
    # Create or update backup information
    if not site_config.backup:
        site_config.backup = SiteBackup()
    
    # Create backup info
    backup_info = SiteBackupInfo(
        time=timestamp,
        file=wordpress_archive,
        database=database_file
    )
    
    # Update the last_backup field
    site_config.backup.last_backup = backup_info
    
    # Save the updated configuration
    set_site_config(domain, site_config)
    
    info(f"📝 Đã cập nhật thông tin backup cho {domain}")
    debug(f"  ⏱️  Thời gian: {timestamp}")
    debug(f"  💾 Database: {database_file}")
    debug(f"  📦 Mã nguồn: {wordpress_archive}")
    
    return True

@log_call
def backup_finalize(domain: str = None):
    backup_path = BACKUP_TEMP_STATE.get("backup_path")
    wordpress_archive = BACKUP_TEMP_STATE.get("wordpress_archive")
    
    if backup_path:
        info(f"✅ Backup hoàn tất.")
        info(f"   📁 Thư mục backup: {backup_path}")
        if wordpress_archive and os.path.exists(wordpress_archive):
            archive_size = os.path.getsize(wordpress_archive) / (1024*1024)
            info(f"   📦 Mã nguồn website: {wordpress_archive} ({archive_size:.2f} MB)")
    else:
        warn("⚠️ Không tìm thấy đường dẫn backup để kết thúc tiến trình.")
    
    BACKUP_TEMP_STATE.clear()

@log_call
def rollback_backup(domain: str = None):
    """
    Roll back all backup operations by removing the backup directory and cleaning up config.json.
    This is sufficient since all backup files are contained within this directory.
    
    Args:
        domain: The domain name of the website being backed up
    """
    # 1. Remove the backup directory
    backup_path = BACKUP_TEMP_STATE.get("backup_path")
    if backup_path and os.path.exists(backup_path):
        shutil.rmtree(backup_path)
        info(f"🗑️ Đã xoá thư mục backup chưa hoàn tất tại: {backup_path}")
    else:
        warn("⚠️ Không có thư mục backup nào để xoá.")
    
    # 2. Clean up backup configuration in config.json
    if domain:
        try:
            # Try to get the site configuration
            site_config = get_site_config(domain)
            if site_config and site_config.backup:
                # Clear backup configuration by setting it to None
                site_config.backup = None
                set_site_config(domain, site_config)
                info(f"🧹 Đã xoá thông tin backup trong cấu hình cho {domain}")
            
            # Alternative approach: just delete the backup key from config.json
            # delete_site_config(domain, "backup")
            # info(f"🧹 Đã xoá thông tin backup trong cấu hình cho {domain}")
        except Exception as e:
            warn(f"⚠️ Không thể xoá thông tin backup trong cấu hình: {e}")
    
    # 3. Clear the state
    BACKUP_TEMP_STATE.clear()
    info("↩️ Đã rollback toàn bộ tiến trình backup.")
