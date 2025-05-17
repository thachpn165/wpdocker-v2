import questionary
from src.features.system.manager import SystemManager


def prompt_rebuild_core_containers():
    mgr = SystemManager()
    containers = mgr.get_core_containers()
    choices = [{"name": c["name"], "value": c["name"]} for c in containers]
    choices.append({"name": "All", "value": "all"})
    selected = questionary.select("Select container to rebuild:", choices=choices).ask()
    if not selected:
        return
    if selected == "all":
        selected = [c["name"] for c in containers]
    else:
        selected = [selected]
    mgr.rebuild_core_containers(selected, interactive=True)
