import shutil
import questionary

# Danh sách editor phổ biến để kiểm tra trên hệ thống
COMMON_EDITORS = [
    "nano", "vim", "nvim", "vi", "micro", "code", "subl", "gedit", "mate"
]

EDITOR_GUIDES = {
    "nano": {
        "Chỉnh sửa nội dung": "Gõ trực tiếp vào vùng nội dung",
        "Xóa nội dung": "Dùng phím Delete hoặc Backspace",
        "Tìm kiếm": "Ctrl + W",
        "Lưu và thoát": "Ctrl + O → Enter, rồi Ctrl + X",
        "Thoát không lưu": "Ctrl + X, sau đó chọn N"
    },
    "vim": {
        "Chỉnh sửa nội dung": "Nhấn i để vào chế độ INSERT",
        "Xóa nội dung": "Ở chế độ INSERT dùng Delete hoặc Backspace",
        "Tìm kiếm": "/ + từ khóa, nhấn Enter",
        "Lưu và thoát": ":wq + Enter",
        "Thoát không lưu": ":q! + Enter"
    },
    "micro": {
        "Chỉnh sửa nội dung": "Gõ trực tiếp vào vùng nội dung",
        "Xóa nội dung": "Dùng phím Delete hoặc Backspace",
        "Tìm kiếm": "Ctrl + F",
        "Lưu và thoát": "Ctrl + S rồi Ctrl + Q",
        "Thoát không lưu": "Ctrl + Q rồi chọn không lưu"
    },
    "vi": {
        "Chỉnh sửa nội dung": "Nhấn i để vào chế độ INSERT",
        "Xóa nội dung": "Ở chế độ INSERT dùng Delete hoặc Backspace",
        "Tìm kiếm": "/ + từ khóa, nhấn Enter",
        "Lưu và thoát": ":wq + Enter",
        "Thoát không lưu": ":q! + Enter"
    }
    # Các editor GUI như code, subl, gedit không cần hướng dẫn CLI
}

def choose_editor(default: str = None) -> str:
    """
    Hiển thị danh sách các editor đang có sẵn trên hệ thống và cho người dùng chọn.
    Nếu default được cung cấp và có sẵn thì sẽ chọn sẵn.
    Sau khi chọn sẽ hiển thị hướng dẫn thao tác và hỏi xác nhận tiếp tục.
    """
    available_editors = [editor for editor in COMMON_EDITORS if shutil.which(editor)]

    if not available_editors:
        print("❌ Không tìm thấy trình soạn thảo nào có sẵn trên hệ thống.")
        return None

    default_choice = default if default in available_editors else available_editors[0]

    selected = questionary.select(
        "Chọn trình soạn thảo để chỉnh sửa:",
        choices=available_editors,
        default=default_choice
    ).ask()

    if selected in EDITOR_GUIDES:
        guide = EDITOR_GUIDES[selected]
        print("\n📘 Hướng dẫn sử dụng trình soạn thảo:")
        for key, val in guide.items():
            print(f"- {key}: {val}")

    confirm = questionary.confirm("Bạn có muốn tiếp tục mở file với trình soạn thảo này không?").ask()
    if not confirm:
        print("❌ Đã huỷ thao tác mở trình soạn thảo.")
        return None

    return selected
