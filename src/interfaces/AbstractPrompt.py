#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Định nghĩa lớp trừu tượng AbstractPrompt cho các prompt tương tác với người dùng.
"""
from abc import ABC, abstractmethod
from src.common.debug import log_call, info, error, warn, debug, success

class AbstractPrompt(ABC):
    """
    Lớp trừu tượng cho các prompt tương tác với người dùng.
    
    Triển khai mẫu thiết kế Template Method để chuẩn hóa 
    quy trình xử lý prompt với 3 bước chính:
    1. Thu thập đầu vào từ người dùng
    2. Xử lý nghiệp vụ dựa trên đầu vào
    3. Hiển thị kết quả cho người dùng
    """
    
    def __init__(self):
        """Khởi tạo prompt."""
        self.result = None
    
    @abstractmethod
    def _collect_inputs(self):
        """
        Thu thập đầu vào từ người dùng.
        
        Return:
            dict hoặc object chứa dữ liệu đầu vào, hoặc None nếu người dùng hủy.
        """
        pass
    
    @abstractmethod
    def _process(self, inputs):
        """
        Xử lý nghiệp vụ dựa trên đầu vào.
        
        Args:
            inputs: Dữ liệu thu thập từ _collect_inputs()
            
        Return:
            dict hoặc object chứa kết quả xử lý
        """
        pass
    
    @abstractmethod
    def _show_results(self):
        """
        Hiển thị kết quả cho người dùng.
        
        Sử dụng self.result để hiển thị kết quả.
        """
        pass
        
    @log_call
    def run(self):
        """
        Chạy các bước của prompt theo thứ tự.
        
        Quy trình:
        1. Thu thập đầu vào từ người dùng
        2. Xử lý nghiệp vụ dựa trên đầu vào
        3. Hiển thị kết quả cho người dùng
        
        Return:
            Kết quả xử lý hoặc None nếu có lỗi
        """
        try:
            # Thu thập đầu vào từ người dùng
            inputs = self._collect_inputs()
            if inputs is None:
                # Người dùng đã hủy thao tác
                return None
                
            # Xử lý nghiệp vụ
            self.result = self._process(inputs)
            
            # Hiển thị kết quả
            if self.result is not None:
                self._show_results()
                
            return self.result
                
        except (KeyboardInterrupt, EOFError):
            print("\nĐã huỷ thao tác.")
            return None
        except Exception as e:
            error(f"❌ Lỗi không xác định: {e}")
            return None