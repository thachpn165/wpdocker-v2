from questionary import select
import os
import glob
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import website_list, get_sites_dir
from core.backend.modules.website.website_utils import get_site_config

@log_call
def prompt_list_backup():
    """
    Hiển thị danh sách các bản backup của website.
    Hiển thị thông tin chi tiết bao gồm thời gian tạo, kích thước, và các file trong backup.
    """
    # Lấy danh sách website
    websites = website_list()
    if not websites:
        error("❌ Không tìm thấy website nào để hiển thị backup.")
        return
    
    # Chọn một website
    domain = select(
        "🌐 Chọn website để xem danh sách backup:",
        choices=websites
    ).ask()
    
    if not domain:
        info("Đã huỷ thao tác xem danh sách backup.")
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
    
    # Tạo bảng hiển thị với thông tin chi tiết về các bản backup
    console = Console()
    
    # Hiển thị thông tin tổng quan
    site_config = get_site_config(domain)
    last_backup_info = None
    if site_config and site_config.backup and site_config.backup.last_backup:
        last_backup_info = site_config.backup.last_backup
    
    # Hiển thị header
    console.print(f"\n[bold cyan]📊 Danh sách backup cho website: [yellow]{domain}[/yellow][/bold cyan]")
    console.print(f"[cyan]📁 Thư mục backup: [yellow]{backup_dir}[/yellow][/cyan]")
    console.print(f"[cyan]🔢 Tổng số bản backup: [yellow]{len(backup_folders)}[/yellow][/cyan]")
    
    # Hiển thị thông tin bản backup gần nhất từ cấu hình (nếu có)
    if last_backup_info:
        console.print("\n[bold green]💾 Thông tin bản backup gần nhất từ cấu hình:[/bold green]")
        console.print(f"[green]⏱️  Thời gian: [yellow]{last_backup_info.time}[/yellow][/green]")
        console.print(f"[green]📦 File mã nguồn: [yellow]{last_backup_info.file}[/yellow][/green]")
        console.print(f"[green]🗄️ File database: [yellow]{last_backup_info.database}[/yellow][/green]")
    
    # Tạo bảng hiển thị chi tiết về các bản backup
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Tên backup", style="cyan")
    table.add_column("Thời gian tạo", style="green")
    table.add_column("Kích thước", style="yellow")
    table.add_column("Trạng thái", style="magenta")
    
    # Sắp xếp các thư mục backup theo thời gian tạo (mới nhất lên đầu)
    backup_folders = sorted(
        backup_folders,
        key=lambda x: os.path.getctime(os.path.join(backup_dir, x)),
        reverse=True
    )
    
    # Điền thông tin vào bảng
    for idx, folder in enumerate(backup_folders, 1):
        folder_path = os.path.join(backup_dir, folder)
        
        # Lấy thời gian tạo
        folder_time = datetime.fromtimestamp(os.path.getctime(folder_path))
        time_str = folder_time.strftime("%d/%m/%Y %H:%M:%S")
        
        # Tính kích thước tổng cộng
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):  # Đảm bảo file vẫn tồn tại
                    total_size += os.path.getsize(fp)
        
        size_str = f"{total_size / (1024*1024):.2f} MB"
        
        # Tìm các file quan trọng trong thư mục backup (để kiểm tra với cấu hình)
        # Chúng ta vẫn cần code này để so sánh với cấu hình, nhưng sẽ không hiển thị trong bảng
        files_list = []
        for file_pattern in ["*.sql", "*.tar.gz", "*.zip"]:
            matches = glob.glob(os.path.join(folder_path, file_pattern))
            for match in matches:
                file_name = os.path.basename(match)
                file_size = os.path.getsize(match) / (1024*1024)
                files_list.append(f"{file_name} ({file_size:.2f} MB)")
        
        # Kiểm tra xem đây có phải là backup gần nhất trong cấu hình không
        status = ""
        if last_backup_info:
            # Kiểm tra xem bản backup này có phải là bản gần nhất trong cấu hình không
            if last_backup_info.file and (last_backup_info.file.startswith(folder_path) or 
                                           (last_backup_info.database and last_backup_info.database.startswith(folder_path))):
                status = "✅ Là bản backup gần nhất"
        
        # Thêm dòng vào bảng
        table.add_row(
            str(idx),
            folder,
            time_str,
            size_str,
            status
        )
    
    # Hiển thị bảng
    console.print("\n")
    console.print(table)
    
    # Hiển thị chú thích
    console.print("\n[dim]📝 Chú thích:[/dim]")
    console.print("[dim]- Bảng được sắp xếp theo thời gian tạo (mới nhất lên đầu)[/dim]")
    console.print("[dim]- Kích thước hiển thị là tổng kích thước của tất cả file trong thư mục backup[/dim]")
    console.print("[dim]- Trạng thái ✅ cho biết đây là bản backup gần nhất được lưu trong cấu hình[/dim]")
    
    # Đợi người dùng nhấn Enter để tiếp tục
    input("\nNhấn Enter để tiếp tục...")