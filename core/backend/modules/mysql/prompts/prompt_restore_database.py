"""
Module xử lý khôi phục database cho website.
"""
from questionary import select, confirm
import os
from rich.text import Text
from core.backend.utils.debug import log_call, info, warn, error, success, debug
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.website_utils import select_website
from core.backend.modules.mysql.import_export import import_database
from core.backend.utils.env_utils import env


class DatabaseRestorePrompt(PromptBase):
    """
    Lớp xử lý prompt khôi phục database website.
    
    Triển khai lớp trừu tượng PromptBase với các phương thức:
    - _collect_inputs: Thu thập thông tin domain, file backup và lựa chọn reset
    - _process: Thực hiện việc khôi phục database
    - _show_results: Hiển thị kết quả khôi phục
    """
    
    def _collect_inputs(self):
        """
        Thu thập đầu vào từ người dùng về website, file backup và lựa chọn reset.
        
        Returns:
            dict: Chứa thông tin domain, file backup và lựa chọn reset hoặc None nếu bị hủy
        """
        # Chọn website để khôi phục
        domain = select_website("🌐 Chọn website để khôi phục database:")
        if not domain:
            info("Đã huỷ thao tác.")
            return None

        # Hỏi có muốn xoá dữ liệu hiện tại không
        reset = confirm(
            "🗑️ Bạn có muốn xoá dữ liệu hiện tại trước khi khôi phục không?"
        ).ask()

        # Hướng dẫn chuẩn bị file backup
        sites_dir = env.get("SITES_DIR", "/opt/wp-docker/data/sites")
        backup_path = os.path.join(sites_dir, domain, "backups")
        
        info(
            f"📁 Vui lòng đảm bảo file SQL đã được đặt trong thư mục: {backup_path}"
        )

        # Kiểm tra thư mục backup đã tồn tại chưa
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)
            success(f"✅ Đã tạo thư mục backup tại: {backup_path}")

        # Xác nhận đã chuẩn bị file
        if not confirm("❓ Bạn đã đặt file SQL vào thư mục backup chưa?").ask():
            info("Đã huỷ thao tác. Hãy chuẩn bị file backup trước.")
            return None

        # Lấy danh sách các file trong thư mục backup
        try:
            backup_files = [f for f in os.listdir(backup_path) if f.endswith('.sql')]
        except Exception as e:
            error(f"❌ Không thể đọc thư mục backup: {e}")
            return None

        if not backup_files:
            error("❌ Không tìm thấy file SQL nào trong thư mục backup.")
            return None

        # Chọn file để khôi phục
        selected_file = select(
            "📦 Chọn file SQL để khôi phục:",
            choices=backup_files
        ).ask()

        if not selected_file:
            info("Đã huỷ thao tác.")
            return None

        # Đường dẫn đầy đủ đến file backup
        db_file = os.path.join(backup_path, selected_file)

        # Xác nhận khôi phục
        if not confirm(f"⚠️ Xác nhận khôi phục database cho {domain} từ file {selected_file}?").ask():
            info("Đã huỷ thao tác khôi phục.")
            return None

        return {
            "domain": domain,
            "db_file": db_file,
            "reset": reset,
            "file_name": selected_file
        }
    
    def _process(self, inputs):
        """
        Thực hiện việc khôi phục database.
        
        Args:
            inputs: Dict chứa thông tin domain, file backup và lựa chọn reset
            
        Returns:
            dict: Kết quả xử lý bao gồm trạng thái thành công và chi tiết khôi phục
        """
        domain = inputs["domain"]
        db_file = inputs["db_file"]
        reset = inputs["reset"]
        file_name = inputs["file_name"]
        
        try:
            # Khôi phục database
            import_database(domain, db_file, reset)
            
            return {
                "domain": domain,
                "success": True,
                "file_name": file_name,
                "reset": reset,
                "error": None
            }
        except Exception as e:
            error_msg = f"❌ Lỗi khi khôi phục database: {e}"
            error(error_msg)
            
            return {
                "domain": domain,
                "success": False,
                "file_name": file_name,
                "reset": reset,
                "error": str(e)
            }
    
    def _show_results(self):
        """
        Hiển thị kết quả khôi phục database.
        
        Sử dụng self.result để hiển thị kết quả xử lý.
        """
        if not self.result:
            return
        
        domain = self.result["domain"]
        success_status = self.result["success"]
        file_name = self.result["file_name"]
        reset = self.result["reset"]
        error_msg = self.result.get("error")
        
        if success_status:
            # Hiển thị thông báo thành công với thông tin chi tiết
            reset_text = "đã xóa dữ liệu cũ" if reset else "giữ nguyên dữ liệu cũ"
            success_message = Text(f"✅ Đã hoàn thành khôi phục database cho website {domain}.")
            success(success_message)
            
            info(f"📊 Thông tin khôi phục:")
            info(f"  • File SQL: {file_name}")
            info(f"  • Dữ liệu cũ: {reset_text}")
        else:
            # Hiển thị thông báo lỗi
            error_message = Text(f"❌ Khôi phục database cho website {domain} thất bại.")
            error(error_message)
            
            if error_msg:
                warn(f"⚠️ Chi tiết lỗi: {error_msg}")


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_restore_database():
    """
    Hàm tiện ích để khôi phục database.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình khôi phục database hoặc None nếu bị hủy
    """
    prompt = DatabaseRestorePrompt()
    return prompt.run()