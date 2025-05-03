"""
Module xử lý xóa backup website.
"""
from questionary import select, confirm, checkbox
import os
import shutil
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.website_utils import select_website, get_site_config, set_site_config
from core.backend.modules.backup.backup_restore import get_backup_folders, get_backup_info

class BackupDeletePrompt(PromptBase):
    """
    Lớp xử lý prompt xóa backup website.
    
    Triển khai lớp trừu tượng PromptBase với các phương thức:
    - _collect_inputs: Thu thập thông tin domain, backup, và lựa chọn xóa
    - _process: Thực hiện việc xóa backup theo lựa chọn
    - _show_results: Hiển thị kết quả xóa backup
    """
    
    def _collect_inputs(self):
        """
        Thu thập đầu vào từ người dùng về website và lựa chọn xóa backup.
        
        Returns:
            dict: Chứa thông tin domain, backup, và lựa chọn xóa hoặc None nếu bị hủy
        """
        # Chọn một website sử dụng hàm select_website có sẵn
        domain = select_website("🌐 Chọn website để xóa backup:")
        
        if not domain:
            # Thông báo lỗi đã được hiển thị trong hàm select_website
            return None
        
        # Lấy thông tin về các thư mục backup
        backup_dir, backup_folders, last_backup_info = get_backup_folders(domain)
        
        if not backup_folders:
            return None  # Thông báo lỗi đã được hiển thị trong hàm get_backup_folders
        
        # Tạo danh sách hiển thị với thông tin thêm về thời gian và kích thước
        display_choices = []
        backup_info_list = []
        
        for folder in backup_folders:
            backup_info = get_backup_info(backup_dir, folder, last_backup_info)
            backup_info_list.append(backup_info)
            
            if "error" in backup_info:
                display_choices.append(f"{folder} (Không thể lấy thông tin: {backup_info['error']})")
            else:
                status = "✅ Là bản backup gần nhất" if backup_info["is_latest"] else ""
                display_choices.append(f"{folder} [{backup_info['time']}] [{backup_info['size']}] {status}")
        
        # Hỏi người dùng muốn xóa một hay nhiều backup
        delete_mode = select(
            "🔍 Bạn muốn xóa backup như thế nào?",
            choices=[
                "Xóa một bản backup",
                "Xóa nhiều bản backup",
                "Xóa tất cả bản backup"
            ]
        ).ask()
        
        if not delete_mode:
            info("Đã huỷ thao tác xóa backup.")
            return None
        
        selected_backups = []
        
        if delete_mode == "Xóa một bản backup":
            # Chọn một backup để xóa
            selected_backup = select(
                "📁 Chọn bản backup để xóa:",
                choices=display_choices
            ).ask()
            
            if not selected_backup:
                info("Đã huỷ thao tác xóa backup.")
                return None
            
            # Lấy thông tin backup đã chọn
            folder_name = selected_backup.split(" ")[0]
            selected_index = next((i for i, item in enumerate(backup_info_list) if item["folder"] == folder_name), -1)
            
            if selected_index == -1:
                error(f"❌ Không tìm thấy thông tin cho bản backup đã chọn.")
                return None
                
            backup_info = backup_info_list[selected_index]
            selected_backups = [backup_info]
            
            if not confirm(f"⚠️ Xác nhận xóa backup {folder_name} của website {domain}?").ask():
                info("Đã huỷ thao tác xóa backup.")
                return None
            
        elif delete_mode == "Xóa nhiều bản backup":
            # Chọn nhiều backup để xóa
            backup_indices = [i for i in range(len(display_choices))]
            backup_choices = [f"{i+1}. {choice}" for i, choice in zip(backup_indices, display_choices)]
            
            selected_backup_choices = checkbox(
                "📁 Chọn các bản backup để xóa (dùng phím space để chọn):",
                choices=backup_choices
            ).ask()
            
            if not selected_backup_choices:
                info("Đã huỷ thao tác xóa backup.")
                return None
            
            # Lấy danh sách các index được chọn
            selected_indices = [int(item.split(".")[0]) - 1 for item in selected_backup_choices]
            for idx in selected_indices:
                if 0 <= idx < len(backup_info_list):
                    selected_backups.append(backup_info_list[idx])
            
            if not selected_backups:
                error("❌ Không có backup nào được chọn để xóa.")
                return None
            
            if not confirm(f"⚠️ Xác nhận xóa {len(selected_backups)} bản backup của website {domain}?").ask():
                info("Đã huỷ thao tác xóa backup.")
                return None
            
        elif delete_mode == "Xóa tất cả bản backup":
            selected_backups = backup_info_list
            
            if not confirm(f"⚠️ CẢNH BÁO: Xác nhận xóa TẤT CẢ {len(backup_folders)} bản backup của website {domain}?").ask():
                info("Đã huỷ thao tác xóa backup.")
                return None
        
        return {
            "domain": domain,
            "delete_mode": delete_mode,
            "selected_backups": selected_backups,
            "backup_dir": backup_dir
        }
    
    def _process(self, inputs):
        """
        Xử lý việc xóa backup dựa trên thông tin đầu vào.
        
        Args:
            inputs: Dict chứa thông tin domain, lựa chọn xóa và danh sách backup
            
        Returns:
            dict: Kết quả xử lý bao gồm trạng thái thành công và chi tiết xóa
        """
        domain = inputs["domain"]
        delete_mode = inputs["delete_mode"]
        selected_backups = inputs["selected_backups"]
        
        deletion_results = []
        success_count = 0
        failed_count = 0
        cleanup_config = False
        
        for backup_info in selected_backups:
            folder = backup_info["folder"]
            folder_path = backup_info["path"]
            result = {
                "folder": folder,
                "success": False,
                "error": None
            }
            
            try:
                shutil.rmtree(folder_path)
                success(f"✅ Đã xóa backup {folder} của website {domain}.")
                result["success"] = True
                success_count += 1
                
                # Kiểm tra xem có cần cập nhật cấu hình backup không
                is_in_config = self._check_backup_in_config(domain, folder_path)
                if is_in_config:
                    cleanup_config = True
            except Exception as e:
                error_msg = f"❌ Lỗi khi xóa backup {folder}: {e}"
                error(error_msg)
                result["success"] = False
                result["error"] = str(e)
                failed_count += 1
            
            deletion_results.append(result)
        
        # Nếu xóa toàn bộ backup hoặc có backup trong cấu hình bị xóa
        if delete_mode == "Xóa tất cả bản backup" or cleanup_config:
            self._cleanup_backup_config(domain)
        
        return {
            "domain": domain,
            "delete_mode": delete_mode,
            "deletion_results": deletion_results,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_count": len(selected_backups),
            "config_cleaned": cleanup_config
        }
    
    def _show_results(self):
        """
        Hiển thị kết quả xóa backup.
        
        Sử dụng self.result để hiển thị kết quả xử lý.
        """
        if not self.result:
            return
        
        domain = self.result["domain"]
        delete_mode = self.result["delete_mode"]
        success_count = self.result["success_count"]
        failed_count = self.result["failed_count"]
        total_count = self.result["total_count"]
        config_cleaned = self.result["config_cleaned"]
        
        # Hiển thị tổng quan kết quả
        if success_count == total_count:
            success(f"🎉 Đã xóa thành công {success_count}/{total_count} bản backup của website {domain}.")
        elif success_count > 0:
            warn(f"⚠️ Đã xóa {success_count}/{total_count} bản backup, {failed_count} bản backup gặp lỗi.")
        else:
            error(f"❌ Không thể xóa bất kỳ bản backup nào của website {domain}.")
        
        # Hiển thị thông tin về cấu hình
        if config_cleaned:
            info(f"🧹 Đã xóa thông tin backup trong cấu hình cho {domain}")
    
    def _check_backup_in_config(self, domain, folder_path):
        """
        Kiểm tra xem backup có tồn tại trong cấu hình hay không.
        
        Args:
            domain (str): Tên domain
            folder_path (str): Đường dẫn thư mục backup
            
        Returns:
            bool: True nếu backup có trong cấu hình, False nếu không
        """
        site_config = get_site_config(domain)
        if not site_config or not site_config.backup or not site_config.backup.last_backup:
            return False
        
        backup_info = site_config.backup.last_backup
        
        # Kiểm tra nếu file trong cấu hình thuộc thư mục đã xóa
        if backup_info.file and backup_info.file.startswith(folder_path):
            return True
        
        return False
    
    def _cleanup_backup_config(self, domain):
        """
        Xóa thông tin backup trong cấu hình.
        
        Args:
            domain (str): Tên domain
        """
        site_config = get_site_config(domain)
        if site_config and site_config.backup:
            site_config.backup = None
            set_site_config(domain, site_config)
            info(f"🧹 Đã xóa thông tin backup trong cấu hình cho {domain}")


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_delete_backup():
    """
    Hàm tiện ích để xóa backup.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình xóa backup hoặc None nếu bị hủy
    """
    prompt = BackupDeletePrompt()
    return prompt.run()