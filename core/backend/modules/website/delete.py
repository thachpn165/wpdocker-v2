

def delete_website(domain):
    """
    Xoá website với tên miền đã cho.
    """
    try:
        # Giả lập việc xoá website
        print(f"Đang xoá website '{domain}'...")
        # Thực hiện các thao tác xoá ở đây
        print(f"Website '{domain}' đã được xoá thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi xoá website '{domain}': {e}")