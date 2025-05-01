from core.backend.modules.website.website_utils import website_list, get_site_config, _is_website_running
from rich.console import Console
from rich.table import Table
from core.backend.utils.debug import log_call

console = Console()

@log_call
def list_website():
    domains = website_list()
    if not domains:
        console.print("[bold red]⚠️ Không có website nào đang hoạt động.")
        return

    table = Table(title="📄 Danh sách website", header_style="bold magenta")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Trạng thái", style="bold green")
    table.add_column("Domain", style="cyan")
    table.add_column("PHP", style="yellow")
    table.add_column("Cache", style="white")

    for index, domain in enumerate(domains, start=1):
        site_config = get_site_config(domain)
        status = _is_website_running(domain) 
        php_version = site_config.php_version if site_config else "-"
        cache = site_config.cache if site_config else "-"
        table.add_row(str(index), status, domain, php_version, cache)

    console.print(table)
    console.print("[bold green]Tổng số website:[/] [yellow]{}[/]".format(len(domains)))