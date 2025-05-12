import subprocess
import sys


def system_tools_menu():
    print("5. Đổi ngôn ngữ (Change Language)")
    choice = input("Chọn chức năng: ")
    if choice == "5":
        subprocess.run([sys.executable, "src/features/system/cli/change_language.py"])
