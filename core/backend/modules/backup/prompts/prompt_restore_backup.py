"""
Module xử lý khôi phục backup website.
"""
from questionary import select, confirm, checkbox
import os
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.website_utils import select_website
from core.backend.modules.backup.backup_manager import BackupManager

class BackupRestorePrompt(PromptBase):
    """
    Lớp xử lý prompt khôi phục backup website.
    
    Triển khai lớp trừu tượng PromptBase với các phương thức:
    - _collect_inputs: Thu thập thông tin domain, backup, và các thành phần cần khôi phục
    - _process: Tiến hành quá trình khôi phục backup
    - _show_results: Hiển thị kết quả khôi phục
    """
    
    def _collect_inputs(self):
        """
        Thu thập đầu vào từ người dùng về website, backup, và các thành phần cần khôi phục.
        
        Returns:
            dict: Chứa thông tin domain, backup, và các tuỳ chọn khôi phục hoặc None nếu bị hủy
        """
        # Khởi tạo BackupManager
        backup_manager = BackupManager()
        
        # Chọn một website sử dụng hàm select_website có sẵn
        domain = select_website("🌐 Chọn website để khôi phục backup:")
        
        if not domain:
            # Thông báo lỗi đã được hiển thị trong hàm select_website
            return None
        
        # Chọn nơi lưu trữ backup
        storage_providers = backup_manager.get_available_providers()
        
        if not storage_providers:
            error("❌ Không tìm thấy nơi lưu trữ backup nào.")
            return None
        
        # Format provider options to be more user-friendly
        provider_choices = []
        for provider in storage_providers:
            if provider == "local":
                provider_choices.append({"name": "Lưu trữ local", "value": provider})
            elif provider.startswith("rclone:"):
                remote_name = provider.split(":")[1]
                provider_choices.append({"name": f"Lưu trữ đám mây ({remote_name})", "value": provider})
            else:
                provider_choices.append({"name": provider, "value": provider})
        
        selected_provider = select(
            "💾 Chọn nơi lưu trữ backup để khôi phục:",
            choices=provider_choices
        ).ask()
        
        if not selected_provider:
            info("Đã huỷ thao tác khôi phục backup.")
            return None
        
        # Lấy danh sách backup từ provider đã chọn
        backups = backup_manager.list_backups(domain, selected_provider)
        
        if not backups:
            error(f"❌ Không tìm thấy backup nào cho website {domain} trong {selected_provider}.")
            return None
        
        # Format backup list for display
        backup_choices = []
        for backup in backups:
            backup_type = "Database" if backup.get("type") == "database" else "Full backup"
            size = backup.get("size_formatted", "Unknown size")
            modified = backup.get("modified_formatted", "Unknown date")
            backup_choices.append({
                "name": f"{backup.get('name')} [{backup_type}] [{size}] [{modified}]",
                "value": backup
            })
        
        # Thêm tuỳ chọn huỷ
        backup_choices.append({"name": "Huỷ", "value": None})
        
        # Chọn một backup để khôi phục
        selected_backup = select(
            "📁 Chọn bản backup để khôi phục:",
            choices=backup_choices
        ).ask()
        
        if not selected_backup:
            info("Đã huỷ thao tác khôi phục backup.")
            return None
        
        backup_name = selected_backup.get("name")
        backup_type = selected_backup.get("type")
        
        info(f"📂 Bạn đã chọn bản backup: {backup_name}")
        
        # Xác nhận khôi phục
        if not confirm(f"⚠️ CẢNH BÁO: Khôi phục sẽ ghi đè lên dữ liệu hiện tại của website {domain}. Bạn có chắc chắn muốn tiếp tục?").ask():
            info("Đã huỷ thao tác khôi phục backup.")
            return None
        
        # Trả về thông tin đã thu thập
        return {
            "domain": domain,
            "backup": selected_backup,
            "provider": selected_provider
        }
    
    def _process(self, inputs):
        """
        Xử lý việc khôi phục backup dựa trên thông tin đầu vào.
        
        Args:
            inputs: Dict chứa thông tin domain, backup và provider
            
        Returns:
            dict: Kết quả xử lý bao gồm trạng thái thành công và chi tiết khôi phục
        """
        domain = inputs["domain"]
        backup = inputs["backup"]
        provider = inputs["provider"]
        
        # Khởi tạo BackupManager
        backup_manager = BackupManager()
        
        # Tiến hành khôi phục
        info(f"🔄 Bắt đầu quá trình khôi phục backup cho website {domain} từ {provider}...")
        
        backup_name = backup.get("name")
        backup_type = backup.get("type")
        
        # Gọi BackupManager để restore backup
        success, message = backup_manager.restore_backup(
            domain, 
            backup_name, 
            provider
        )
        
        # Trả về kết quả
        return {
            "domain": domain,
            "backup": backup,
            "provider": provider,
            "restore_success": success,
            "message": message
        }
    
    def _show_results(self):
        """
        Hiển thị kết quả khôi phục backup.
        
        Sử dụng self.result để hiển thị kết quả xử lý.
        """
        if not self.result:
            return
        
        domain = self.result["domain"]
        backup = self.result["backup"]
        provider = self.result["provider"]
        restore_success = self.result["restore_success"]
        message = self.result["message"]
        
        # Format provider name for display
        provider_display = provider
        if provider == "local":
            provider_display = "lưu trữ local"
        elif provider.startswith("rclone:"):
            remote_name = provider.split(":")[1]
            provider_display = f"lưu trữ đám mây ({remote_name})"
        
        # Format backup name for display
        backup_name = backup.get("name", "Unknown")
        backup_type = "Database" if backup.get("type") == "database" else "Full backup"
        
        # Tổng hợp kết quả và hiển thị
        if restore_success:
            success(f"🎉 Đã hoàn tất khôi phục backup cho website {domain}.")
            info(f"✅ Đã khôi phục từ: {backup_name} [{backup_type}] từ {provider_display}")
        else:
            error(f"❌ Quá trình khôi phục backup gặp lỗi: {message}")
            info(f"❌ Không thể khôi phục: {backup_name} [{backup_type}] từ {provider_display}")


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_restore_backup():
    """
    Hàm tiện ích để chạy prompt khôi phục backup.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình khôi phục hoặc None nếu bị hủy
    """
    prompt = BackupRestorePrompt()
    return prompt.run()