"""
Quản lý cấu hình hệ thống.

Module này cung cấp lớp ConfigManager để quản lý truy cập, lưu trữ và cập nhật
cấu hình của hệ thống.
"""

import os
import json
from typing import Any, Dict, Optional, List, Union

from src.common.logging import Debug, error, debug, log_call
from src.common.utils.environment import env
from src.core.models.core_config import CoreConfig


class ConfigManager:
    """Quản lý cấu hình hệ thống.
    
    Lớp này quản lý truy cập đến tệp tin cấu hình chính của hệ thống,
    cung cấp các phương thức để đọc, ghi và cập nhật cấu hình.
    
    Thiết kế theo mẫu Singleton để đảm bảo chỉ có một phiên bản duy nhất
    của ConfigManager tồn tại trong ứng dụng.
    """
    
    _instance = None
    
    def __new__(cls) -> 'ConfigManager':
        """
        Đảm bảo rằng chỉ có một phiên bản của ConfigManager được tạo.
        
        Returns:
            ConfigManager: Phiên bản duy nhất của ConfigManager
        """
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Khởi tạo ConfigManager."""
        if self._initialized:
            return
            
        self._initialized = True
        self.debug = Debug("ConfigManager")
        
        # Đường dẫn tệp tin cấu hình - ưu tiên sử dụng thư mục /data/config
        default_config_dir = os.path.join(env.get("DATA_DIR", "/opt/wp-docker/data"), "config")
        self.config_dir = env.get("CONFIG_DIR", default_config_dir)
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Đảm bảo thư mục cấu hình tồn tại
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Nạp cấu hình
        self._config = self._load_config()
        
        self.debug.info(f"Đã nạp cấu hình từ {self.config_file}")
    
    @log_call
    def _load_config(self) -> Dict[str, Any]:
        """
        Nạp cấu hình từ tệp tin.

        Returns:
            Dict[str, Any]: Dữ liệu cấu hình
        """
        # Tạo cấu hình trống nếu tệp tin không tồn tại để buộc bootstrap hỏi người dùng
        if not os.path.exists(self.config_file):
            self.debug.info(f"Tệp tin cấu hình không tồn tại, tạo mới (hoàn toàn trống): {self.config_file}")
            # Cấu hình hoàn toàn trống để buộc bootstrap hỏi người dùng tất cả các cài đặt
            empty_config = {}

            # Lưu cấu hình trống
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(empty_config, f, indent=2, ensure_ascii=False)

            return empty_config
        
        # Nạp cấu hình từ tệp tin
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.debug.error(f"Lỗi phân tích cú pháp JSON: {str(e)}")
            # Sao lưu tệp tin gặp sự cố và tạo mới
            backup_file = f"{self.config_file}.bak"
            try:
                import shutil
                shutil.copy2(self.config_file, backup_file)
                self.debug.info(f"Đã sao lưu tệp tin cấu hình gặp sự cố vào {backup_file}")
            except Exception as backup_err:
                self.debug.error(f"Không thể sao lưu tệp tin cấu hình: {str(backup_err)}")
            
            # Trả về cấu hình mặc định
            return {
                "core": {
                    "channel": "stable",
                    "timezone": "Asia/Ho_Chi_Minh",
                    "webserver": "nginx",
                    "lang": "vi"
                }
            }
        except Exception as e:
            self.debug.error(f"Lỗi không xác định khi nạp cấu hình: {str(e)}")
            return {
                "core": {
                    "channel": "stable",
                    "timezone": "Asia/Ho_Chi_Minh",
                    "webserver": "nginx",
                    "lang": "vi"
                }
            }
    
    @log_call
    def reload(self) -> None:
        """Nạp lại cấu hình từ tệp tin."""
        self._config = self._load_config()
        self.debug.info("Đã nạp lại cấu hình")
    
    @log_call
    def get(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Lấy giá trị từ cấu hình.
        
        Args:
            key: Đường dẫn của khóa, sử dụng ký hiệu dấu chấm (vd: "core.channel")
                 Nếu key là None, trả về toàn bộ cấu hình
            default: Giá trị mặc định nếu không tìm thấy khóa
            
        Returns:
            Giá trị của khóa hoặc giá trị mặc định nếu không tìm thấy
        """
        # Nếu không có khóa, trả về toàn bộ cấu hình
        if key is None:
            return self._config
        
        # Tách đường dẫn thành các phần
        parts = key.split('.')
        
        # Bắt đầu từ cấu hình gốc
        current = self._config
        
        # Duyệt qua các phần của đường dẫn
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Không tìm thấy phần nào trên đường dẫn, trả về giá trị mặc định
                return default
        
        # Trả về giá trị tìm thấy
        return current
    
    @log_call
    def set(self, key: str, value: Any) -> None:
        """
        Thiết lập giá trị cho một khóa trong cấu hình.
        
        Args:
            key: Đường dẫn của khóa, sử dụng ký hiệu dấu chấm (vd: "core.channel")
            value: Giá trị cần thiết lập
        """
        # Tách đường dẫn thành các phần
        parts = key.split('.')
        
        # Bắt đầu từ cấu hình gốc
        current = self._config
        
        # Duyệt qua các phần của đường dẫn trừ phần cuối cùng
        for i, part in enumerate(parts[:-1]):
            # Tạo các phần của đường dẫn nếu chúng chưa tồn tại
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Thiết lập giá trị cho phần cuối cùng của đường dẫn
        current[parts[-1]] = value
        
        # Lưu cấu hình
        self.save()
    
    @log_call
    def save(self) -> bool:
        """
        Lưu cấu hình vào tệp tin.
        
        Returns:
            bool: True nếu lưu thành công, False nếu thất bại
        """
        try:
            # Tạo thư mục cấu hình nếu chưa tồn tại
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Lưu cấu hình vào tệp tin
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            self.debug.info(f"Đã lưu cấu hình vào {self.config_file}")
            return True
        except Exception as e:
            self.debug.error(f"Lỗi khi lưu cấu hình: {str(e)}")
            return False
    
    @log_call
    def update_key(self, key: str, value: Any) -> bool:
        """
        Cập nhật một phần của cấu hình.
        
        Phương thức này cho phép cập nhật cả một phần của cấu hình,
        không chỉ giá trị lá. Hữu ích khi cần cập nhật toàn bộ đối tượng
        cấu hình con.
        
        Args:
            key: Khóa cấu hình (không sử dụng ký hiệu dấu chấm)
            value: Giá trị mới
            
        Returns:
            bool: True nếu cập nhật thành công, False nếu thất bại
        """
        try:
            self._config[key] = value
            return self.save()
        except Exception as e:
            self.debug.error(f"Lỗi khi cập nhật khóa {key}: {str(e)}")
            return False
    
    @log_call
    def delete(self, key: str) -> bool:
        """
        Xóa một khóa từ cấu hình.
        
        Args:
            key: Đường dẫn của khóa cần xóa, sử dụng ký hiệu dấu chấm
            
        Returns:
            bool: True nếu xóa thành công, False nếu thất bại hoặc không tìm thấy khóa
        """
        # Tách đường dẫn thành các phần
        parts = key.split('.')
        
        # Bắt đầu từ cấu hình gốc
        current = self._config
        
        # Duyệt qua các phần của đường dẫn trừ phần cuối cùng
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                # Không tìm thấy khóa
                return False
            current = current[part]
        
        # Xóa khóa nếu nó tồn tại
        if parts[-1] in current:
            del current[parts[-1]]
            return self.save()
        
        return False
    
    @log_call
    def get_core_config(self) -> CoreConfig:
        """
        Lấy cấu hình core dưới dạng đối tượng CoreConfig.
        
        Returns:
            CoreConfig: Đối tượng cấu hình core
        """
        # Lấy dữ liệu cấu hình core
        core_data = self.get("core", {})
        
        # Khởi tạo CoreConfig từ dữ liệu
        core_config = CoreConfig(
            channel=core_data.get("channel", "stable"),
            timezone=core_data.get("timezone", "Asia/Ho_Chi_Minh"),
            webserver=core_data.get("webserver", "nginx"),
            lang=core_data.get("lang", "vi"),
            containers=None  # Chưa hỗ trợ containers
        )
        
        return core_config
    
    @log_call
    def update_core_config(self, core_config: CoreConfig) -> bool:
        """
        Cập nhật cấu hình core từ đối tượng CoreConfig.
        
        Args:
            core_config: Đối tượng cấu hình core
            
        Returns:
            bool: True nếu cập nhật thành công, False nếu thất bại
        """
        try:
            # Chuyển đổi CoreConfig thành từ điển
            core_dict = {
                "channel": core_config.channel,
                "timezone": core_config.timezone,
                "webserver": core_config.webserver,
                "lang": core_config.lang
            }
            
            # Nếu có containers, thêm vào cấu hình
            if core_config.containers:
                import jsons
                core_dict["containers"] = jsons.dump(core_config.containers)
            
            # Cập nhật cấu hình
            self._config["core"] = core_dict
            return self.save()
        except Exception as e:
            self.debug.error(f"Lỗi khi cập nhật cấu hình core: {str(e)}")
            return False
    
    @log_call
    def backup(self, backup_suffix: str = "backup") -> Optional[str]:
        """
        Tạo bản sao lưu của tệp tin cấu hình.
        
        Args:
            backup_suffix: Hậu tố thêm vào tên tệp tin sao lưu
            
        Returns:
            Optional[str]: Đường dẫn đến tệp tin sao lưu nếu thành công, None nếu thất bại
        """
        try:
            backup_file = f"{self.config_file}.{backup_suffix}"
            import shutil
            shutil.copy2(self.config_file, backup_file)
            self.debug.info(f"Đã sao lưu cấu hình vào {backup_file}")
            return backup_file
        except Exception as e:
            self.debug.error(f"Lỗi khi sao lưu cấu hình: {str(e)}")
            return None