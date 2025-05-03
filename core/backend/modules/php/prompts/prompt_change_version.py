"""
Module xử lý thay đổi phiên bản PHP cho website.
"""
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.php.change_version import php_change_version
from core.backend.modules.website.website_utils import select_website
from core.backend.utils.debug import log_call, info, error, success, warn, debug
from core.backend.modules.php.utils import php_choose_version

class ChangePhpVersionPrompt(PromptBase):
    """
    Lớp xử lý prompt thay đổi phiên bản PHP cho website.
    
    Triển khai lớp trừu tượng PromptBase với các phương thức:
    - _collect_inputs: Thu thập thông tin domain và phiên bản PHP mới
    - _process: Thực hiện việc thay đổi phiên bản PHP
    - _show_results: Hiển thị kết quả thay đổi
    """
    
    def _collect_inputs(self):
        """
        Thu thập đầu vào từ người dùng về website và phiên bản PHP mới.
        
        Returns:
            dict: Chứa thông tin domain và phiên bản PHP mới hoặc None nếu bị hủy
        """
        domain = select_website("Chọn website để thay đổi phiên bản PHP:")
        if not domain:
            info("Đã huỷ thao tác thay đổi phiên bản PHP.")
            return None

        new_php_version = php_choose_version()
        if not new_php_version:
            info("Đã huỷ thao tác thay đổi phiên bản PHP.")
            return None
            
        return {
            "domain": domain,
            "new_php_version": new_php_version
        }
    
    def _process(self, inputs):
        """
        Thực hiện việc thay đổi phiên bản PHP.
        
        Args:
            inputs: Dict chứa thông tin domain và phiên bản PHP mới
            
        Returns:
            dict: Kết quả xử lý bao gồm trạng thái thành công và chi tiết thay đổi
        """
        domain = inputs["domain"]
        new_php_version = inputs["new_php_version"]
        
        try:
            # Thực hiện thay đổi phiên bản PHP
            result = php_change_version(domain, new_php_version)
            
            return {
                "domain": domain,
                "new_php_version": new_php_version,
                "success": True,
                "error": None,
                "result": result
            }
        except Exception as e:
            error_msg = f"❌ Lỗi khi thay đổi phiên bản PHP cho website {domain}: {e}"
            error(error_msg)
            
            return {
                "domain": domain,
                "new_php_version": new_php_version,
                "success": False,
                "error": str(e)
            }
    
    def _show_results(self):
        """
        Hiển thị kết quả thay đổi phiên bản PHP.
        
        Sử dụng self.result để hiển thị kết quả xử lý.
        """
        if not self.result:
            return
        
        domain = self.result["domain"]
        new_php_version = self.result["new_php_version"]
        success_status = self.result["success"]
        
        if success_status:
            success(f"✅ Đã thay đổi phiên bản PHP cho website {domain} thành công.")
            info(f"📦 Phiên bản PHP mới: {new_php_version}")
        else:
            error_msg = self.result.get("error", "Lỗi không xác định")
            warn(f"⚠️ Vui lòng kiểm tra lại cấu hình và thử lại.")


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_change_php_version():
    """
    Hàm tiện ích để thay đổi phiên bản PHP cho website.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình thay đổi phiên bản PHP hoặc None nếu bị hủy
    """
    prompt = ChangePhpVersionPrompt()
    return prompt.run()