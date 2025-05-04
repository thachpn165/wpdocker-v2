"""
Module hiển thị prompt để backup website.
"""
from questionary import select, confirm, checkbox
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.website_utils import website_list
from core.backend.modules.backup.backup_manager import BackupManager

class BackupWebsitePrompt(PromptBase):
    """
    Lớp xử lý prompt backup website.
    
    Triển khai lớp trừu tượng PromptBase với các phương thức:
    - _collect_inputs: Thu thập thông tin domain cần backup
    - _process: Thực hiện việc backup website
    - _show_results: Hiển thị kết quả backup
    """
    
    def _collect_inputs(self):
        """
        Thu thập đầu vào từ người dùng về website cần backup.
        
        Returns:
            dict: Chứa thông tin domain, provider, và danh sách domain cần backup, hoặc None nếu bị hủy
        """
        # Lấy danh sách website
        websites = website_list()
        if not websites:
            error("❌ Không tìm thấy website nào để backup.")
            return None
        
        # Hỏi người dùng muốn backup một hay nhiều website
        backup_mode = select(
            "🔍 Bạn muốn backup website như thế nào?",
            choices=[
                "Backup một website",
                "Backup nhiều website"
            ]
        ).ask()
        
        if not backup_mode:
            info("Đã huỷ thao tác backup.")
            return None
        
        selected_domains = []
        
        if backup_mode == "Backup một website":
            # Chọn một website
            domain = select(
                "🌐 Chọn website cần backup:",
                choices=websites
            ).ask()
            
            if not domain:
                info("Đã huỷ thao tác backup.")
                return None
                
            selected_domains = [domain]
        else:
            # Chọn nhiều website
            selected_domains = checkbox(
                "🌐 Chọn các website cần backup (dùng phím space để chọn):",
                choices=websites
            ).ask()
            
            if not selected_domains:
                info("Không có website nào được chọn để backup.")
                return None
        
        # Chọn nơi lưu trữ backup
        backup_manager = BackupManager()
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
            "💾 Chọn nơi lưu trữ backup:",
            choices=provider_choices
        ).ask()
        
        if not selected_provider:
            info("Đã huỷ thao tác backup.")
            return None
        
        # Confirm backup operation
        if backup_mode == "Backup một website":
            if not confirm(f"⚠️ Xác nhận backup website {selected_domains[0]} lưu trữ tại {selected_provider}?").ask():
                info("Đã huỷ thao tác backup.")
                return None
        else:
            if not confirm(f"⚠️ Xác nhận backup {len(selected_domains)} website lưu trữ tại {selected_provider}?").ask():
                info("Đã huỷ thao tác backup.")
                return None
        
        return {
            "backup_mode": backup_mode,
            "domains": selected_domains,
            "provider": selected_provider
        }
    
    def _process(self, inputs):
        """
        Thực hiện việc backup website dựa trên thông tin đầu vào.
        
        Args:
            inputs: Dict chứa thông tin domain, provider, và danh sách domain cần backup
            
        Returns:
            dict: Kết quả xử lý bao gồm trạng thái thành công và chi tiết backup
        """
        backup_mode = inputs["backup_mode"]
        domains = inputs["domains"]
        provider = inputs["provider"]
        
        # Initialize the BackupManager
        backup_manager = BackupManager()
        
        backup_results = []
        success_count = 0
        
        for domain in domains:
            result = {
                "domain": domain,
                "success": False,
                "error": None,
                "provider": provider,
                "backup_path": None
            }
            
            info(f"⏳ Đang tiến hành backup website {domain} lưu trữ tại {provider}...")
            
            try:
                success, backup_path = backup_manager.create_backup(domain, provider)
                
                result["success"] = success
                result["backup_path"] = backup_path
                
                if success:
                    success_count += 1
                    
                    if backup_mode == "Backup nhiều website":
                        success(f"✅ Backup website {domain} hoàn tất (lưu tại {provider}).")
                else:
                    result["error"] = backup_path  # In case of error, the message is in backup_path
                    if backup_mode == "Backup nhiều website":
                        error(f"❌ Lỗi khi backup website {domain}: {backup_path}")
            except Exception as e:
                error_msg = f"❌ Lỗi khi backup website {domain}: {e}"
                error(error_msg)
                result["success"] = False
                result["error"] = str(e)
            
            backup_results.append(result)
        
        return {
            "backup_mode": backup_mode,
            "results": backup_results,
            "total_count": len(domains),
            "success_count": success_count,
            "failed_count": len(domains) - success_count,
            "provider": provider
        }
    
    def _show_results(self):
        """
        Hiển thị kết quả backup website.
        
        Sử dụng self.result để hiển thị kết quả xử lý.
        """
        if not self.result:
            return
        
        backup_mode = self.result["backup_mode"]
        results = self.result["results"]
        total_count = self.result["total_count"]
        success_count = self.result["success_count"]
        failed_count = self.result["failed_count"]
        provider = self.result["provider"]
        
        # Format provider name for display
        provider_display = provider
        if provider == "local":
            provider_display = "lưu trữ local"
        elif provider.startswith("rclone:"):
            remote_name = provider.split(":")[1]
            provider_display = f"lưu trữ đám mây ({remote_name})"
        
        # Hiển thị tổng quan kết quả nếu là backup nhiều website
        if backup_mode == "Backup nhiều website":
            if success_count == total_count:
                success(f"🎉 Đã hoàn tất backup tất cả {total_count} website thành công ({provider_display}).")
            elif success_count > 0:
                warn(f"⚠️ Đã backup {success_count}/{total_count} website, {failed_count} website gặp lỗi ({provider_display}).")
            else:
                error(f"❌ Không thể backup bất kỳ website nào.")
        # Nếu là backup một website, thông báo đã được hiển thị trong quá trình xử lý
        else:
            domain = results[0]["domain"]
            if results[0]["success"]:
                backup_path = results[0].get("backup_path", "")
                success(f"✅ Hoàn tất backup website {domain} ({provider_display}).")
                info(f"📦 Backup lưu tại: {backup_path}")
            else:
                error_msg = results[0].get("error", "Lỗi không xác định")
                error(f"❌ Backup website {domain} thất bại: {error_msg}")


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_backup_website():
    """
    Hàm tiện ích để backup website.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình backup hoặc None nếu bị hủy
    """
    prompt = BackupWebsitePrompt()
    return prompt.run()