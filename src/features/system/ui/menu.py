import subprocess
import sys


def system_tools_menu():
    print("5. Change Language")
    choice = input("Select function: ")
    if choice == "5":
        subprocess.run([sys.executable, "src/features/system/cli/change_language.py"])
