# File: core/menu/main.py
import sys
from rich.console import Console
from rich.text import Text
from core.backend.objects.menu import Menu, MenuItem
from core.backend.modules.website.prompts.create_prompt import prompt_create_website
from core.backend.modules.website.prompts.delete_prompt import prompt_delete_website
from core.backend.modules.website.prompts.list_prompt import prompt_list_website
from core.backend.modules.website.prompts.restart_prompt import prompt_restart_website
from core.backend.modules.website.prompts.logs_prompt import prompt_watch_logs
from core.backend.modules.website.prompts.info_prompt import prompt_info_website
from core.backend.modules.ssl.prompts.install_prompt import prompt_install_ssl
from core.backend.modules.ssl.prompts.check_prompt import prompt_check_ssl
from core.backend.modules.php.prompts.prompt_change_version import prompt_change_php_version
from core.backend.modules.php.prompts.prompt_edit_config import prompt_edit_config
from core.backend.modules.php.prompts.prompt_install_extension import prompt_install_php_extension
from core.backend.modules.mysql.edit_config import edit_mysql_config
from core.backend.modules.mysql.prompts.prompt_restore_database import prompt_restore_database
from core.backend.modules.ssl.prompts.edit_prompt import prompt_edit_ssl
from core.backend.modules.backup.prompts.prompt_backup_website import prompt_backup_website
from core.backend.modules.backup.prompts.prompt_delete_backup import prompt_delete_backup
from core.backend.modules.backup.prompts.prompt_list_backup import prompt_list_backup
from core.backend.modules.backup.prompts.prompt_restore_backup import prompt_restore_backup
from core.backend.modules.backup.prompts.prompt_schedule_backup import prompt_schedule_backup
from core.backend.modules.cron.cron_manager import CronManager

console = Console()

def display_header():
    header = Text("""

    ██╗    ██╗██████╗     ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
    ██║    ██║██╔══██╗    ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
    ██║ █╗ ██║██████╔╝    ██████╔╝██║   ██║██║     █████╔╝ █████╗  ██████╔╝
    ██║███╗██║██╔═══╝     ██╔═══╝ ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
    ╚███╔███╔╝██║         ██║     ╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
     ╚══╝╚══╝ ╚═╝         ╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    ═══════════════════════════════════════════════════════════════════════════════
    """, style="cyan")
    console.print(header)

def show_main_menu():
    display_header()
    menu = Menu(
        title="\n📋 Chọn chức năng cần sử dụng:",
        items=[
            MenuItem("1", "Quản lý Website", website_menu),
            MenuItem("2", "Quản lý Chứng chỉ SSL", ssl_menu),
            MenuItem("3", "Công cụ hệ thống", system_menu),
            MenuItem("4", "Quản lý RClone", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("5", "Công cụ WordPress", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("6", "Quản lý Backup", backup_menu),
            MenuItem("7", "Cài đặt Cache WP", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("8", "Quản lý PHP", php_menu),
            MenuItem("9", "Quản lý MySQL", database_menu),
            MenuItem("10", "Kiểm tra & cập nhật WP Docker", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("0", "Thoát", lambda: sys.exit(console.print("👋 Tạm biệt!", style="bold green")))
        ],
        back_id="0"
    )
    menu.display()

def website_menu():
    menu = Menu(
        title="\n🌐 Quản lý Website:",
        items=[
            MenuItem("1", "Tạo website", prompt_create_website),
            MenuItem("2", "Xóa website", prompt_delete_website),
            MenuItem("3", "Xem danh sách website", prompt_list_website),
            MenuItem("4", "Restart lại website", prompt_restart_website),
            MenuItem("5", "Xem logs website", prompt_watch_logs),
            MenuItem("6", "Xem thông tin website", prompt_info_website),
            MenuItem("7", "Migrate dữ liệu về WP Docker", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

def ssl_menu():
    menu = Menu(
        title="\n🔒 Quản lý Chứng chỉ SSL:",
        items=[
            MenuItem("1", "Tạo chứng chỉ tự ký", lambda: prompt_install_ssl("selfsigned")),
            MenuItem("2", "Tạo chứng chỉ Lets Encrypt (Miễn phí)", lambda: prompt_install_ssl("letsencrypt")),
            MenuItem("3", "Cài chứng chỉ thủ công (trả phí)", lambda: prompt_install_ssl("manual")),
            MenuItem("4", "Kiểm tra thông tin chứng chỉ", prompt_check_ssl),
            MenuItem("5", "Sửa chứng chỉ hiện tại", prompt_edit_ssl), 
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

def system_menu():
    menu = Menu(
        title="\n⚙️ Công cụ hệ thống:",
        items=[
            MenuItem("1", "Rebuild lại container core", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("2", "Cập nhật phiên bản WP Docker", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("3", "Xem thông tin hệ thống", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("4", "Đổi ngôn ngữ", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("5", "Đổi kênh phiên bản", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("6", "Dọn dẹp Docker", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("7", "Quản lý công việc tự động", cron_menu),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

def rclone_menu():
    menu = Menu(
        title="\n📦 Quản lý RClone:",
        items=[
            MenuItem("1", "Cấu hình RClone", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("2", "Sao lưu dữ liệu lên Google Drive", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("3", "Phục hồi dữ liệu từ Google Drive", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

def backup_menu():
    menu = Menu(
        title="\n💾 Quản lý Backup:",
        items=[
            MenuItem("1", "Tạo backup website", prompt_backup_website),
            MenuItem("2", "Phục hồi backup", prompt_restore_backup),
            MenuItem("3", "Xem danh sách backup", prompt_list_backup),
            MenuItem("4", "Xóa backup", prompt_delete_backup),
            MenuItem("5", "Lên lịch backup tự động", prompt_schedule_backup),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

def cron_menu():
    menu = Menu(
        title="\n⏱️ Quản lý công việc tự động:",
        items=[
            MenuItem("1", "Xem danh sách công việc", cron_list_jobs),
            MenuItem("2", "Kích hoạt/Vô hiệu hóa công việc", cron_toggle_job),
            MenuItem("3", "Xóa công việc", cron_remove_job),
            MenuItem("4", "Thực thi công việc ngay", cron_run_job),
            MenuItem("0", "Quay lại menu hệ thống", None)
        ],
        back_id="0"
    )
    menu.display()

def cron_list_jobs():
    """Hiển thị danh sách các công việc cron đã đăng ký."""
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        console.print("Không có công việc nào được đăng ký.", style="yellow")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    console.print("\n[bold cyan]⏱️ Danh sách công việc tự động:[/bold cyan]")
    console.print("-" * 80)
    console.print(f"{'ID':<15} {'Loại':<10} {'Lịch trình':<15} {'Trạng thái':<15} {'Mục tiêu':<20}")
    console.print("-" * 80)
    
    for job in jobs:
        status = "[green]✅ Kích hoạt[/green]" if job.enabled else "[red]❌ Vô hiệu[/red]"
        console.print(f"{job.id:<15} {job.job_type:<10} {job.schedule:<15} {status:<15} {job.target_id:<20}")
    
    console.print("-" * 80)
    console.print(f"Tổng số: {len(jobs)} công việc")
    
    input("\nNhấn Enter để tiếp tục...")

def cron_toggle_job():
    """Kích hoạt hoặc vô hiệu hóa một công việc cron."""
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        console.print("Không có công việc nào được đăng ký.", style="yellow")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Hiển thị danh sách các công việc
    console.print("\n[bold cyan]⏱️ Danh sách công việc tự động:[/bold cyan]")
    
    job_choices = {}
    for i, job in enumerate(jobs, 1):
        status = "✅ Kích hoạt" if job.enabled else "❌ Vô hiệu"
        choice = f"{i}. {job.id} - {job.job_type} - {job.target_id} - {status}"
        job_choices[choice] = job
    
    from questionary import select
    selected = select(
        "Chọn công việc để kích hoạt/vô hiệu hóa:",
        choices=list(job_choices.keys()) + ["❌ Quay lại"]
    ).ask()
    
    if not selected or selected == "❌ Quay lại":
        return
    
    job = job_choices[selected]
    
    # Đảo trạng thái
    if job.enabled:
        manager.disable_job(job.id)
        console.print(f"✅ Đã vô hiệu hóa công việc {job.id}", style="green")
    else:
        manager.enable_job(job.id)
        console.print(f"✅ Đã kích hoạt công việc {job.id}", style="green")
    
    input("\nNhấn Enter để tiếp tục...")

def cron_remove_job():
    """Xóa một công việc cron."""
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        console.print("Không có công việc nào được đăng ký.", style="yellow")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Hiển thị danh sách các công việc
    console.print("\n[bold cyan]⏱️ Danh sách công việc tự động:[/bold cyan]")
    
    job_choices = {}
    for i, job in enumerate(jobs, 1):
        status = "✅ Kích hoạt" if job.enabled else "❌ Vô hiệu"
        choice = f"{i}. {job.id} - {job.job_type} - {job.target_id} - {status}"
        job_choices[choice] = job
    
    from questionary import select, confirm
    selected = select(
        "Chọn công việc để xóa:",
        choices=list(job_choices.keys()) + ["❌ Quay lại"]
    ).ask()
    
    if not selected or selected == "❌ Quay lại":
        return
    
    job = job_choices[selected]
    
    # Xác nhận xóa
    if confirm(f"⚠️ Xác nhận xóa công việc {job.id}?").ask():
        manager.remove_job(job.id)
        console.print(f"✅ Đã xóa công việc {job.id}", style="green")
    else:
        console.print("Đã hủy thao tác xóa.", style="yellow")
    
    input("\nNhấn Enter để tiếp tục...")

def cron_run_job():
    """Chạy một công việc cron ngay lập tức."""
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        console.print("Không có công việc nào được đăng ký.", style="yellow")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Hiển thị danh sách các công việc
    console.print("\n[bold cyan]⏱️ Danh sách công việc tự động:[/bold cyan]")
    
    job_choices = {}
    for i, job in enumerate(jobs, 1):
        status = "✅ Kích hoạt" if job.enabled else "❌ Vô hiệu"
        choice = f"{i}. {job.id} - {job.job_type} - {job.target_id} - {status}"
        job_choices[choice] = job
    
    from questionary import select, confirm
    selected = select(
        "Chọn công việc để chạy ngay:",
        choices=list(job_choices.keys()) + ["❌ Quay lại"]
    ).ask()
    
    if not selected or selected == "❌ Quay lại":
        return
    
    job = job_choices[selected]
    
    # Xác nhận chạy
    if confirm(f"⚠️ Xác nhận chạy công việc {job.id} ngay bây giờ?").ask():
        console.print(f"🔄 Đang chạy công việc {job.id}...", style="yellow")
        manager.run_job(job.id)
        console.print(f"✅ Đã thực thi công việc {job.id}", style="green")
    else:
        console.print("Đã hủy thao tác chạy.", style="yellow")
    
    input("\nNhấn Enter để tiếp tục...")

def php_menu():
    menu = Menu(
        title="\n🐘 Quản lý PHP:",
        items=[
            MenuItem("1", "Thay đổi phiên bản PHP", prompt_change_php_version),
            MenuItem("2", "Sửa cấu hình PHP", prompt_edit_config),
            MenuItem("3", "Cài PHP Extension", prompt_install_php_extension),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

def database_menu():
    menu = Menu(
        title="\n🗄️ Quản lý Database:",
        items=[
            MenuItem("1", "Sửa cấu hình MySQL", edit_mysql_config),
            MenuItem("2", "Phục hồi database", prompt_restore_database),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()