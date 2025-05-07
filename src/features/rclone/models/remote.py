"""
Model cho remote configuration.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class RemoteConfig:
    """Model lưu trữ thông tin cấu hình remote."""
    name: str
    type: str
    params: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemoteConfig':
        """Tạo đối tượng từ dictionary."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            params=data.get("params", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đối tượng thành dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "params": self.params
        }
    
    def get_display_type(self) -> str:
        """Lấy tên hiển thị của loại remote."""
        type_map = {
            "s3": "S3 (Amazon S3, Wasabi, etc.)",
            "drive": "Google Drive",
            "dropbox": "Dropbox",
            "onedrive": "Microsoft OneDrive",
            "sftp": "SFTP",
            "ftp": "FTP",
            "webdav": "WebDAV / Nextcloud",
            "b2": "Backblaze B2",
            "box": "Box",
            "azureblob": "Azure Blob Storage"
        }
        return type_map.get(self.type, self.type) 