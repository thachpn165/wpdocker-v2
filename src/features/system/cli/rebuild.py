import click
from src.features.system.manager import SystemManager


@click.command("rebuild-core")
@click.option("--containers", multiple=True, help="Names of containers to rebuild (leave empty to rebuild all)")
def rebuild_core_cli(containers):
    """
    Rebuild core containers.
    """
    mgr = SystemManager()
    all_containers = [c["name"] for c in mgr.get_core_containers()]
    if not containers:
        containers = all_containers
    mgr.rebuild_core_containers(list(containers), interactive=False)
