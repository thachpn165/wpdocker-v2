"""
Module hiển thị danh sách các website đã được tạo.
"""
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.list import list_website
from core.backend.utils.debug import log_call

class ListWebsitePrompt(PromptBase):
    """
    Lớp xử lý prompt hiển thị danh sách website.
    
    Triển khai lớp trừu tượng PromptBase với các phương thức:
    - _collect_inputs: Không cần thu thập đầu vào
    - _process: Gọi hàm list_website để hiển thị danh sách
    - _show_results: Không cần hiển thị kết quả bổ sung
    """
    
    def _collect_inputs(self):
        """
        Không cần thu thập đầu vào.
        
        Returns:
            dict: Dictionary rỗng vì không cần đầu vào
        """
        return {}
    
    def _process(self, inputs):
        """
        Gọi hàm list_website để hiển thị danh sách.
        
        Args:
            inputs: Không sử dụng
            
        Returns:
            dict: Kết quả xử lý
        """
        websites = list_website()
        return {
            "websites": websites
        }
    
    def _show_results(self):
        """
        Không cần hiển thị kết quả bổ sung vì đã được hiển thị trong hàm list_website.
        """
        pass  # Kết quả đã được hiển thị trong hàm list_website


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_list_website():
    """
    Hàm tiện ích để hiển thị danh sách website.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình liệt kê danh sách website
    """
    prompt = ListWebsitePrompt()
    return prompt.run()