import os
from rich.console import Console
from rich.table import Table
from rich.text import Text
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.website.website_utils import select_website
from core.backend.modules.backup.backup_restore import get_backup_folders, get_backup_info

@log_call
def prompt_list_backup():
    """
    Hiển thị danh sách các bản backup của website.
    Hiển thị thông tin chi tiết bao gồm thời gian tạo, kích thước và trạng thái.
    """
    # Chọn một website sử dụng hàm select_website có sẵn
    domain = select_website("🌐 Chọn website để xem danh sách backup:")
    
    if not domain:
        # Thông báo lỗi đã được hiển thị trong hàm select_website
        return
    
    # Lấy thông tin về các thư mục backup
    backup_dir, backup_folders, last_backup_info = get_backup_folders(domain)
    
    if not backup_folders:
        return  # Thông báo lỗi đã được hiển thị trong hàm get_backup_folders
    
    # Tạo bảng hiển thị với thông tin chi tiết về các bản backup
    console = Console()
    
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
    
    # Lấy thông tin chi tiết về mỗi backup và điền vào bảng
    for idx, folder in enumerate(backup_folders, 1):
        backup_info = get_backup_info(backup_dir, folder, last_backup_info)
        
        if "error" in backup_info:
            # Thêm dòng với thông tin lỗi
            table.add_row(
                str(idx),
                folder,
                "Lỗi",
                "Lỗi",
                f"Lỗi: {backup_info['error']}"
            )
        else:
            # Thêm dòng với thông tin đầy đủ
            status = "✅ Là bản backup gần nhất" if backup_info["is_latest"] else ""
            
            table.add_row(
                str(idx),
                backup_info["folder"],
                backup_info["time"],
                backup_info["size"],
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