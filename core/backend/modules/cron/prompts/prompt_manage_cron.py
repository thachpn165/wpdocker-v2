"""
Management prompts for cron jobs.
"""
from rich.console import Console
from questionary import select, confirm
from core.backend.utils.debug import log_call
from core.backend.modules.cron.cron_manager import CronManager

console = Console()

def cron_list_jobs():
    """Hiển thị danh sách các công việc cron đã đăng ký."""
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        console.print("Không có công việc nào được đăng ký.", style="yellow")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    console.print("\n[bold cyan]📋 Danh sách công việc tự động:[/bold cyan]")
    console.print("-" * 80)
    console.print(f"{'ID':<15} {'Loại':<10} {'Lịch trình':<15} {'Trạng thái':<15} {'Mục tiêu':<20}")
    console.print("-" * 80)
    
    for job in jobs:
        status = "[green]✔ Kích hoạt[/green]" if job.enabled else "[red]✘ Vô hiệu[/red]"
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
    console.print("\n[bold cyan]📋 Danh sách công việc tự động:[/bold cyan]")
    
    job_choices = {}
    for i, job in enumerate(jobs, 1):
        status = "✔ Kích hoạt" if job.enabled else "✘ Vô hiệu"
        choice = f"{i}. {job.id} - {job.job_type} - {job.target_id} - {status}"
        job_choices[choice] = job
    
    selected = select(
        "Chọn công việc để kích hoạt/vô hiệu hóa:",
        choices=list(job_choices.keys()) + ["⬅ Quay lại"]
    ).ask()
    
    if not selected or selected == "⬅ Quay lại":
        return
    
    job = job_choices[selected]
    
    # Đảo trạng thái
    if job.enabled:
        manager.disable_job(job.id)
        console.print(f"✔ Đã vô hiệu hóa công việc {job.id}", style="green")
    else:
        manager.enable_job(job.id)
        console.print(f"✔ Đã kích hoạt công việc {job.id}", style="green")
    
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
    console.print("\n[bold cyan]📋 Danh sách công việc tự động:[/bold cyan]")
    
    job_choices = {}
    for i, job in enumerate(jobs, 1):
        status = "✔ Kích hoạt" if job.enabled else "✘ Vô hiệu"
        choice = f"{i}. {job.id} - {job.job_type} - {job.target_id} - {status}"
        job_choices[choice] = job
    
    selected = select(
        "Chọn công việc để xóa:",
        choices=list(job_choices.keys()) + ["⬅ Quay lại"]
    ).ask()
    
    if not selected or selected == "⬅ Quay lại":
        return
    
    job = job_choices[selected]
    
    # Xác nhận xóa
    if confirm(f"❓ Xác nhận xóa công việc {job.id}?").ask():
        manager.remove_job(job.id)
        console.print(f"✔ Đã xóa công việc {job.id}", style="green")
    else:
        console.print("❌ Hủy thao tác xóa.", style="yellow")
    
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
    console.print("\n[bold cyan]📋 Danh sách công việc tự động:[/bold cyan]")
    
    job_choices = {}
    for i, job in enumerate(jobs, 1):
        status = "✔ Kích hoạt" if job.enabled else "✘ Vô hiệu"
        choice = f"{i}. {job.id} - {job.job_type} - {job.target_id} - {status}"
        job_choices[choice] = job
    
    selected = select(
        "Chọn công việc để chạy ngay:",
        choices=list(job_choices.keys()) + ["⬅ Quay lại"]
    ).ask()
    
    if not selected or selected == "⬅ Quay lại":
        return
    
    job = job_choices[selected]
    
    # Xác nhận chạy
    if confirm(f"❓ Xác nhận chạy công việc {job.id} ngay bây giờ?").ask():
        console.print(f"⏳ Đang chạy công việc {job.id}...", style="yellow")
        manager.run_job(job.id)
        console.print(f"✔ Đã thực thi công việc {job.id}", style="green")
    else:
        console.print("❌ Hủy thao tác chạy.", style="yellow")
    
    input("\nNhấn Enter để tiếp tục...")