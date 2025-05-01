import questionary
from rich.console import Console

console = Console()

class MenuItem:
    def __init__(self, id: str, label: str, action):
        self.id = id
        self.label = label
        self.action = action

    def __str__(self):
        return f"⏎ {self.label}" if self.id == "0" else f"[{self.id}] {self.label}"

class Menu:
    def __init__(self, title: str, items: list[MenuItem], back_id: str = "0"):
        self.title = title
        self.items = items
        self.back_id = back_id

    def display(self):
        while True:
            choices = [str(item) for item in self.items]
            answer = questionary.select(
                self.title,
                choices=choices
            ).ask()

            selected_item = next((item for item in self.items if str(item) == answer), None)
            if not selected_item:
                return

            if selected_item.id == self.back_id:
                return  # Exit immediately

            console.print(f"👉 [yellow]Bạn chọn:[/] {selected_item.label}")
            if callable(selected_item.action):
                selected_item.action()

            # Không yêu cầu nhấn Enter sau khi chọn Back
            if selected_item.id != self.back_id:
                input("\n⏎ Nhấn Enter để quay lại menu...")
