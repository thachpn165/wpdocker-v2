"""
Module hiển thị prompt để backup website.
"""
from questionary import select, confirm, checkbox
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.website_utils import website_list
from core.backend.modules.backup.website_backup import backup_website

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
            dict: Chứa thông tin domain hoặc danh sách domain cần backup, hoặc None nếu bị hủy
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
                
            if not confirm(f"⚠️ Xác nhận backup website {domain}?").ask():
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
                
            if not confirm(f"⚠️ Xác nhận backup {len(selected_domains)} website?").ask():
                info("Đã huỷ thao tác backup.")
                return None
        
        return {
            "backup_mode": backup_mode,
            "domains": selected_domains
        }
    
    def _process(self, inputs):
        """
        Thực hiện việc backup website dựa trên thông tin đầu vào.
        
        Args:
            inputs: Dict chứa thông tin domain hoặc danh sách domain cần backup
            
        Returns:
            dict: Kết quả xử lý bao gồm trạng thái thành công và chi tiết backup
        """
        backup_mode = inputs["backup_mode"]
        domains = inputs["domains"]
        
        backup_results = []
        success_count = 0
        
        for domain in domains:
            result = {
                "domain": domain,
                "success": False,
                "error": None
            }
            
            info(f"⏳ Đang tiến hành backup website {domain}...")
            
            try:
                backup_website(domain)
                result["success"] = True
                success_count += 1
                
                if backup_mode == "Backup nhiều website":
                    success(f"✅ Backup website {domain} hoàn tất.")
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
            "failed_count": len(domains) - success_count
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
        
        # Hiển thị tổng quan kết quả nếu là backup nhiều website
        if backup_mode == "Backup nhiều website":
            if success_count == total_count:
                success(f"🎉 Đã hoàn tất backup tất cả {total_count} website thành công.")
            elif success_count > 0:
                warn(f"⚠️ Đã backup {success_count}/{total_count} website, {failed_count} website gặp lỗi.")
            else:
                error(f"❌ Không thể backup bất kỳ website nào.")
        # Nếu là backup một website, thông báo đã được hiển thị trong quá trình xử lý
        else:
            domain = results[0]["domain"]
            if results[0]["success"]:
                success(f"✅ Hoàn tất backup website {domain}.")
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