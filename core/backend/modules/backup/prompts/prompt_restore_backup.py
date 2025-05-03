from questionary import select, confirm, checkbox
import os
import glob
import tarfile
import shutil
import subprocess
from datetime import datetime
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import website_list, get_sites_dir, get_site_config
from core.backend.modules.mysql.import_export import import_database
from core.backend.objects.container import Container

@log_call
def prompt_restore_backup():
    """
    Hiển thị prompt để người dùng chọn và khôi phục backup của website.
    """
    # Lấy danh sách website
    websites = website_list()
    if not websites:
        error("❌ Không tìm thấy website nào để khôi phục backup.")
        return
    
    # Chọn một website
    domain = select(
        "🌐 Chọn website để khôi phục backup:",
        choices=websites
    ).ask()
    
    if not domain:
        info("Đã huỷ thao tác khôi phục backup.")
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
    
    # Tạo danh sách hiển thị với thông tin thêm về thời gian và kích thước
    display_choices = []
    for folder in backup_folders:
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
            status = ""
            if last_backup_info and last_backup_info.file:
                if last_backup_info.file.startswith(folder_path):
                    status = "✅ Là bản backup gần nhất"
            
            display_choices.append(f"{folder} [{time_str}] [{size_str}] {status}")
        except Exception as e:
            display_choices.append(f"{folder} (Không thể lấy thông tin: {e})")
    
    # Chọn một backup để khôi phục
    selected_backup = select(
        "📁 Chọn bản backup để khôi phục:",
        choices=display_choices
    ).ask()
    
    if not selected_backup:
        info("Đã huỷ thao tác khôi phục backup.")
        return
    
    # Lấy tên thư mục từ lựa chọn được hiển thị
    folder_name = selected_backup.split(" ")[0]
    folder_path = os.path.join(backup_dir, folder_name)
    
    # Hiển thị thông tin chi tiết về bản backup đã chọn
    info(f"📂 Bạn đã chọn bản backup: {folder_name}")
    
    # Tìm kiếm các file trong thư mục backup
    archive_file = None
    sql_file = None
    
    for file_path in glob.glob(os.path.join(folder_path, "*.tar.gz")):
        archive_file = file_path
        break
    
    for file_path in glob.glob(os.path.join(folder_path, "*.sql")):
        sql_file = file_path
        break
    
    # Kiểm tra xem có file cần thiết không
    if not archive_file and not sql_file:
        error(f"❌ Không tìm thấy file backup (tar.gz hoặc sql) trong thư mục {folder_name}.")
        return
    
    # Cho người dùng chọn các thành phần để khôi phục
    components = []
    
    if archive_file:
        components.append("Mã nguồn website")
    
    if sql_file:
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
    if "Database" in selected_components and sql_file:
        info(f"💾 Khôi phục database từ file: {os.path.basename(sql_file)}")
        
        # Hỏi người dùng có muốn xóa database hiện tại không
        reset_db = confirm("🗑️ Bạn có muốn xóa dữ liệu database hiện tại trước khi khôi phục?").ask()
        
        try:
            # Sử dụng hàm import_database để khôi phục
            import_database(domain, sql_file, reset=reset_db)
            success(f"✅ Đã khôi phục database thành công.")
        except Exception as e:
            error(f"❌ Lỗi khi khôi phục database: {e}")
            restore_success = False
    
    # Khôi phục mã nguồn
    if "Mã nguồn website" in selected_components and archive_file:
        info(f"📦 Khôi phục mã nguồn từ file: {os.path.basename(archive_file)}")
        
        # Lấy đường dẫn đến thư mục wordpress của website
        wordpress_dir = os.path.join(sites_dir, domain, "wordpress")
        
        if not os.path.exists(wordpress_dir):
            error(f"❌ Không tìm thấy thư mục wordpress cho website {domain}.")
        else:
            try:
                # Tạo một thư mục tạm thời để giải nén
                temp_dir = os.path.join(sites_dir, domain, "temp_extract")
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                os.makedirs(temp_dir)
                
                # Giải nén file tar.gz
                with tarfile.open(archive_file, "r:gz") as tar:
                    tar.extractall(path=temp_dir)
                
                # Lấy tên của PHP container để thiết lập quyền
                php_container_name = f"{domain}-php"
                php_container = Container(name=php_container_name)
                
                if not php_container.running():
                    warn(f"⚠️ Container PHP ({php_container_name}) không hoạt động. Có thể cần phải khởi động lại website sau khi khôi phục.")
                
                # Hỏi người dùng xác nhận
                if confirm(f"⚠️ Quá trình này sẽ GHI ĐÈ lên tất cả file trong thư mục {wordpress_dir}. Tiếp tục?").ask():
                    # Di chuyển các file từ thư mục giải nén vào thư mục wordpress
                    extracted_wordpress_dir = os.path.join(temp_dir, "wordpress")
                    
                    # Xóa thư mục wordpress hiện tại
                    shutil.rmtree(wordpress_dir)
                    
                    # Di chuyển thư mục giải nén vào vị trí mới
                    shutil.move(extracted_wordpress_dir, wordpress_dir)
                    
                    # Thiết lập quyền
                    if php_container.running():
                        try:
                            php_container.exec(["chown", "-R", "www-data:www-data", "/var/www/html"], user="root")
                            info("✅ Đã thiết lập quyền cho các file.")
                        except Exception as e:
                            warn(f"⚠️ Không thể thiết lập quyền: {e}")
                    
                    success(f"✅ Đã khôi phục mã nguồn thành công.")
                else:
                    info("Đã huỷ thao tác khôi phục mã nguồn.")
                
                # Xóa thư mục tạm
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
            except Exception as e:
                error(f"❌ Lỗi khi khôi phục mã nguồn: {e}")
                restore_success = False
    
    # Hỏi người dùng có muốn khởi động lại website không
    if restore_success:
        if confirm(f"🔄 Bạn có muốn khởi động lại website {domain} không?").ask():
            try:
                # Khởi động lại container website bằng docker-compose
                compose_dir = os.path.join(sites_dir, domain, "docker-compose")
                if os.path.exists(compose_dir):
                    cmd = ["docker-compose", "-f", os.path.join(compose_dir, "docker-compose.yml"), "restart"]
                    subprocess.run(cmd, check=True)
                    success(f"✅ Đã khởi động lại website {domain} thành công.")
                else:
                    warn(f"⚠️ Không tìm thấy thư mục docker-compose cho website {domain}.")
            except Exception as e:
                error(f"❌ Lỗi khi khởi động lại website: {e}")
        
        success(f"🎉 Đã hoàn tất khôi phục backup cho website {domain}.")
    else:
        error(f"❌ Quá trình khôi phục backup gặp một số lỗi. Vui lòng kiểm tra lại website {domain}.")