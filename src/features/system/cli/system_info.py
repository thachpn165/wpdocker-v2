import click
from rich.console import Console
from src.features.system.utils.system_info import show_system_info_table


@click.command("system-info")
def view_system_info_cli():
    """Hiển thị thông tin hệ thống (CLI)."""
    console = Console()
    show_system_info_table(console)
