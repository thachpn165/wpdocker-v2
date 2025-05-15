"""
Hỗ trợ quản lý thông tin phiên bản.

Module này cung cấp các hàm tiện ích để truy cập và quản lý thông tin phiên bản
của ứng dụng, thay thế việc sử dụng version.py.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from src.common.logging import debug, error, info, log_call
from src.common.config.manager import ConfigManager


# Các giá trị mặc định cho thông tin phiên bản
DEFAULT_VERSION = "0.1.4"
DEFAULT_CHANNEL = "stable"
DEFAULT_BUILD_DATE = "2023-06-01" 
DEFAULT_DISPLAY_NAME = f"{DEFAULT_VERSION} ({DEFAULT_CHANNEL.capitalize()})"


@log_call
def initialize_version_info() -> None:
    """
    Khởi tạo thông tin phiên bản trong config nếu chưa tồn tại.
    
    Hàm này sẽ đảm bảo rằng thông tin phiên bản luôn tồn tại trong config,
    ngay cả khi config mới được tạo hoặc bị reset.
    """
    config = ConfigManager()
    
    # Kiểm tra xem đã có thông tin phiên bản trong config chưa
    current_version = config.get("core.version")
    
    # Nếu chưa có, khởi tạo với giá trị mặc định
    if not current_version:
        debug("Khởi tạo thông tin phiên bản trong config...")
        config.set("core.version", DEFAULT_VERSION)
        config.set("core.channel", DEFAULT_CHANNEL)
        config.set("core.build_date", DEFAULT_BUILD_DATE)
        config.set("core.display_name", DEFAULT_DISPLAY_NAME)
        config.save()
        debug("Đã khởi tạo thông tin phiên bản trong config")


@log_call
def get_version() -> str:
    """
    Lấy số phiên bản hiện tại.
    
    Returns:
        str: Số phiên bản (vd: "0.1.4")
    """
    config = ConfigManager()
    return config.get("core.version", DEFAULT_VERSION)


@log_call
def get_channel() -> str:
    """
    Lấy kênh phát hành hiện tại.
    
    Returns:
        str: Kênh phát hành ("stable", "nightly", "dev")
    """
    config = ConfigManager()
    return config.get("core.channel", DEFAULT_CHANNEL)


@log_call
def get_build_date() -> str:
    """
    Lấy ngày build của phiên bản hiện tại.
    
    Returns:
        str: Ngày build (vd: "2023-06-01")
    """
    config = ConfigManager()
    return config.get("core.build_date", DEFAULT_BUILD_DATE)


@log_call
def get_display_name() -> str:
    """
    Lấy tên hiển thị của phiên bản hiện tại.
    
    Returns:
        str: Tên hiển thị (vd: "0.1.4 Stable" hoặc "Nightly Build 20230802")
    """
    config = ConfigManager()
    version = get_version()
    channel = get_channel()
    
    # Ưu tiên sử dụng tên hiển thị đã lưu nếu có
    display_name = config.get("core.display_name")
    if display_name:
        return display_name
    
    # Nếu không có, tạo tên mặc định dựa trên version và channel
    return f"{version} ({channel.capitalize()})"


@log_call
def get_version_metadata() -> Dict[str, Any]:
    """
    Lấy metadata của phiên bản hiện tại.
    
    Returns:
        Dict[str, Any]: Metadata của phiên bản hoặc dict rỗng nếu không có
    """
    config = ConfigManager()
    metadata = config.get("core.metadata", {})
    return metadata


@log_call
def get_version_info() -> Dict[str, str]:
    """
    Lấy toàn bộ thông tin phiên bản.
    
    Returns:
        Dict[str, str]: Thông tin phiên bản đầy đủ
    """
    info = {
        "version": get_version(),
        "channel": get_channel(),
        "build_date": get_build_date(),
        "display_name": get_display_name()
    }
    
    # Thêm metadata nếu có
    metadata = get_version_metadata()
    if metadata:
        info["metadata"] = metadata
        
        # Thêm các thông tin bổ sung nếu có trong metadata
        if "code_name" in metadata:
            info["code_name"] = metadata["code_name"]
        if "build_number" in metadata:
            info["build_number"] = metadata["build_number"]
    
    return info


@log_call
def update_version_info(version: str, channel: str = None, build_date: str = None, 
                       display_name: str = None, metadata: Dict[str, Any] = None) -> None:
    """
    Cập nhật thông tin phiên bản trong config.
    
    Args:
        version: Số phiên bản mới
        channel: Kênh phát hành mới (nếu không cung cấp, giữ nguyên giá trị hiện tại)
        build_date: Ngày build mới (nếu không cung cấp, sử dụng ngày hiện tại)
        display_name: Tên hiển thị mới (nếu không cung cấp, tạo tự động)
        metadata: Thông tin metadata bổ sung
    """
    config = ConfigManager()
    
    # Cập nhật version (bắt buộc)
    config.set("core.version", version)
    
    # Cập nhật channel nếu có
    if channel:
        config.set("core.channel", channel)
    else:
        channel = config.get("core.channel", DEFAULT_CHANNEL)
    
    # Cập nhật build_date nếu có, nếu không sử dụng ngày hiện tại
    if build_date:
        config.set("core.build_date", build_date)
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        config.set("core.build_date", today)
    
    # Cập nhật metadata nếu có
    if metadata:
        config.set("core.metadata", metadata)
        debug(f"Đã cập nhật metadata phiên bản: {metadata}")
    
    # Cập nhật display_name nếu có
    if display_name:
        config.set("core.display_name", display_name)
    else:
        # Tạo display_name tự động nếu không cung cấp
        # Ưu tiên sử dụng code_name từ metadata nếu có
        auto_display_name = version
        
        if metadata and "code_name" in metadata:
            auto_display_name = f"{version} \"{metadata['code_name']}\""
        else:
            auto_display_name = f"{version} ({channel.capitalize()})"
            
        # Thêm build number nếu có
        if metadata and "build_number" in metadata:
            auto_display_name += f" (Build {metadata['build_number']})"
            
        config.set("core.display_name", auto_display_name)
    
    # Lưu thay đổi
    config.save()
    debug(f"Đã cập nhật thông tin phiên bản: {version} ({channel})")


@log_call
def parse_version_metadata_from_release(release_body: str) -> Dict[str, Any]:
    """
    Parse metadata phiên bản từ nội dung của release.
    
    Tìm kiếm phần metadata trong định dạng:
    <!-- VERSION_INFO
    {
        "display_name": "Nightly Build 20230802",
        "code_name": "Thunder",
        "other_info": "value"
    }
    -->
    
    Hoặc định dạng đơn giản hơn:
    <!-- VERSION_INFO display_name: "Nightly Build 20230802" code_name: "Thunder" -->
    
    Args:
        release_body: Nội dung mô tả của release
        
    Returns:
        Dict[str, Any]: Metadata phiên bản hoặc dict rỗng nếu không tìm thấy
    """
    if not release_body:
        return {}
    
    # Tìm kiếm metadata trong định dạng <!-- VERSION_INFO ... -->
    pattern = r'<!--\s*VERSION_INFO\s*([\s\S]*?)\s*-->'
    match = re.search(pattern, release_body)
    
    if not match:
        debug("Không tìm thấy metadata VERSION_INFO trong nội dung release")
        return {}
    
    # Lấy nội dung từ phần tìm thấy
    content = match.group(1).strip()
    
    # Thử parse JSON trước
    try:
        # Kiểm tra nếu nội dung bắt đầu bằng { và kết thúc bằng }, đây có thể là JSON
        if content.startswith('{') and content.endswith('}'):
            metadata = json.loads(content)
            info(f"Đã parse metadata phiên bản từ JSON: {metadata}")
            return metadata
    except json.JSONDecodeError:
        # Nếu không phải JSON, tiếp tục với cách khác
        debug("Nội dung không phải là JSON hợp lệ, thử phương pháp khác")
    
    # Thử parse định dạng đơn giản key: "value" key2: "value2"
    try:
        # Sử dụng regex để tìm các cặp key: "value"
        simple_pattern = r'(\w+):\s*"([^"]*)"'
        simple_matches = re.findall(simple_pattern, content)
        
        if simple_matches:
            metadata = {key: value for key, value in simple_matches}
            info(f"Đã parse metadata phiên bản từ định dạng đơn giản: {metadata}")
            return metadata
    except Exception as e:
        error(f"Lỗi parse metadata phiên bản định dạng đơn giản: {str(e)}")
    
    # Thử tìm kiếm các thông tin quan trọng
    try:
        metadata = {}
        
        # Tìm display_name nếu có
        display_match = re.search(r'display_name[=:]\s*"([^"]*)"', content, re.IGNORECASE)
        if display_match:
            metadata["display_name"] = display_match.group(1)
        
        # Tìm code_name nếu có
        code_name_match = re.search(r'code_name[=:]\s*"([^"]*)"', content, re.IGNORECASE)
        if code_name_match:
            metadata["code_name"] = code_name_match.group(1)
        
        # Tìm build_number nếu có
        build_match = re.search(r'build_number[=:]\s*"?(\d+)"?', content, re.IGNORECASE)
        if build_match:
            metadata["build_number"] = build_match.group(1)
        
        if metadata:
            info(f"Đã trích xuất được một số metadata từ phân tích nội dung: {metadata}")
            return metadata
    except Exception as e:
        error(f"Lỗi trích xuất metadata từ nội dung: {str(e)}")
    
    # Nếu tất cả cách trên đều thất bại, trả về dict rỗng
    debug("Không thể parse metadata từ nội dung, trả về dict rỗng")
    return {}


@log_call
def extract_metadata_from_tag_name(tag_name: str) -> Dict[str, Any]:
    """
    Trích xuất metadata từ tên tag, đặc biệt hữu ích cho các bản nightly build.
    
    Hỗ trợ các định dạng:
    - nightly-YYYYMMDD
    - vX.Y.Z-nightly.YYYYMMDD
    - vX.Y.Z-alpha.N
    - vX.Y.Z-beta.N
    - vX.Y.Z-rc.N
    
    Args:
        tag_name: Tên tag cần trích xuất metadata
        
    Returns:
        Dict[str, Any]: Metadata đã trích xuất
    """
    metadata = {}
    
    if not tag_name:
        return metadata
    
    # Loại bỏ tiền tố 'v' nếu có
    if tag_name.startswith('v'):
        version = tag_name[1:]
    else:
        version = tag_name
    
    # Trích xuất ngày từ nightly tag
    nightly_date_pattern = r'(nightly[.-])?(\d{8})'
    nightly_match = re.search(nightly_date_pattern, tag_name)
    if nightly_match:
        date_str = nightly_match.group(2)
        try:
            # Định dạng lại ngày thành YYYY-MM-DD
            date_formatted = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            metadata["build_date"] = date_formatted
            
            # Tạo tên hiển thị cho nightly build
            formatted_date = f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
            metadata["display_name"] = f"Nightly Build {formatted_date}"
            debug(f"Đã trích xuất ngày từ nightly tag: {formatted_date}")
        except Exception as e:
            error(f"Lỗi khi định dạng ngày từ tag: {str(e)}")
    
    # Trích xuất thông tin prerelease
    prerelease_pattern = r'-(alpha|beta|rc)\.?(\d+)'
    prerelease_match = re.search(prerelease_pattern, tag_name)
    if prerelease_match:
        prerelease_type = prerelease_match.group(1)
        prerelease_number = prerelease_match.group(2)
        
        metadata["prerelease_type"] = prerelease_type
        metadata["prerelease_number"] = prerelease_number
        
        # Tạo tên hiển thị cho phiên bản prerelease
        base_version = version.split('-')[0]
        prerelease_display = f"{prerelease_type.capitalize()} {prerelease_number}"
        metadata["display_name"] = f"{base_version} {prerelease_display}"
        debug(f"Đã trích xuất thông tin prerelease: {prerelease_type} {prerelease_number}")
    
    # Trích xuất thông tin build (nếu có)
    build_pattern = r'\+build\.(\d+)'
    build_match = re.search(build_pattern, tag_name)
    if build_match:
        build_number = build_match.group(1)
        metadata["build_number"] = build_number
        debug(f"Đã trích xuất số build: {build_number}")
    
    return metadata


@log_call
def extract_metadata_from_release(release_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trích xuất metadata đầy đủ từ dữ liệu release của GitHub.
    
    Hàm này kết hợp cả thông tin từ các metadata được chèn có chủ đích và
    các thông tin có thể suy ra từ tên tag, tên release và mô tả.
    
    Args:
        release_data: Dữ liệu của release từ GitHub API
        
    Returns:
        Dict[str, Any]: Metadata đầy đủ đã trích xuất
    """
    metadata = {}
    
    if not release_data:
        return metadata
    
    # Lấy các thông tin cơ bản từ release
    tag_name = release_data.get("tag_name", "")
    release_name = release_data.get("name", "")
    is_prerelease = release_data.get("prerelease", False)
    published_at = release_data.get("published_at", "")
    release_body = release_data.get("body", "")
    
    # 1. Đầu tiên, parse metadata có chủ đích từ nội dung release
    embedded_metadata = parse_version_metadata_from_release(release_body)
    if embedded_metadata:
        metadata.update(embedded_metadata)
        info(f"Đã tìm thấy metadata nhúng trong mô tả release: {embedded_metadata}")
    
    # 2. Trích xuất metadata từ tên tag
    tag_metadata = extract_metadata_from_tag_name(tag_name)
    if tag_metadata:
        # Chỉ cập nhật các trường chưa có trong metadata nhúng
        for key, value in tag_metadata.items():
            if key not in metadata:
                metadata[key] = value
        debug(f"Đã bổ sung metadata từ tên tag: {tag_metadata}")
    
    # 3. Sử dụng tên release và thông tin release
    # Nếu chưa có display_name, sử dụng tên release nếu có
    if "display_name" not in metadata and release_name and release_name != tag_name:
        # Loại bỏ tiền tố không cần thiết nếu có
        display_name = release_name
        for prefix in ["WP Docker v2 ", "WP Docker ", "wpdocker-v2-", "wpdocker-"]:
            if display_name.startswith(prefix):
                display_name = display_name[len(prefix):]
                break
        metadata["display_name"] = display_name
        debug(f"Sử dụng tên release làm display_name: {display_name}")
    
    # 4. Xác định kênh phát hành
    if "channel" not in metadata:
        if is_prerelease or "nightly" in tag_name.lower() or "alpha" in tag_name.lower() or "beta" in tag_name.lower() or "rc" in tag_name.lower():
            metadata["channel"] = "nightly"
        else:
            metadata["channel"] = "stable"
        debug(f"Xác định kênh phát hành: {metadata['channel']}")
    
    # 5. Xác định ngày build
    if "build_date" not in metadata and published_at:
        try:
            # Định dạng lại ngày từ ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
            from datetime import datetime
            pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            metadata["build_date"] = pub_date.strftime("%Y-%m-%d")
            debug(f"Sử dụng ngày phát hành làm build_date: {metadata['build_date']}")
        except Exception as e:
            error(f"Lỗi khi định dạng ngày phát hành: {str(e)}")
    
    # 6. Trích xuất version từ tag_name nếu chưa có
    if "version" not in metadata and tag_name:
        version = tag_name.lstrip("v")
        # Loại bỏ phần prerelease và build metadata theo semver
        semver_pattern = r'^(\d+\.\d+\.\d+)(?:-|$)'
        semver_match = re.match(semver_pattern, version)
        if semver_match:
            version = semver_match.group(1)
            metadata["version"] = version
            debug(f"Trích xuất version từ tag_name: {version}")
    
    # 7. Tạo display_name đẹp hơn nếu chưa có
    if "display_name" not in metadata:
        # Tạo display_name từ các thành phần khác
        if "version" in metadata:
            base_version = metadata["version"]
            
            # Nếu là phiên bản nightly, tạo tên hiển thị phong phú hơn
            if metadata.get("channel") == "nightly":
                if "build_date" in metadata:
                    # Định dạng lại ngày để hiển thị thân thiện hơn
                    try:
                        date_parts = metadata["build_date"].split("-")
                        if len(date_parts) == 3:
                            formatted_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                            display_name = f"Nightly Build {formatted_date}"
                            
                            # Thêm code_name nếu có
                            if "code_name" in metadata:
                                display_name += f" \"{metadata['code_name']}\""
                                
                            metadata["display_name"] = display_name
                            info(f"Tạo display_name cho nightly build: {display_name}")
                    except Exception as e:
                        debug(f"Lỗi khi định dạng ngày cho display_name: {str(e)}")
                        
                        # Fallback đơn giản
                        display_name = f"Nightly Build - {base_version}"
                        if "code_name" in metadata:
                            display_name += f" \"{metadata['code_name']}\""
                        metadata["display_name"] = display_name
            else:
                # Cho phiên bản stable, sử dụng version và code_name nếu có
                display_name = base_version
                if "code_name" in metadata:
                    display_name += f" \"{metadata['code_name']}\""
                metadata["display_name"] = display_name
                debug(f"Tạo display_name từ version: {display_name}")
    
    # 8. Bổ sung các thông tin bổ sung cho nightly builds
    if metadata.get("channel") == "nightly" and "display_name" in metadata:
        # Đảm bảo hiển thị đúng rằng đây là bản nightly nếu chưa có trong tên
        current_display = metadata["display_name"]
        if "nightly" not in current_display.lower() and "build" not in current_display.lower():
            metadata["display_name"] = f"Nightly Build - {current_display}"
        
        # Thêm build number nếu có và chưa nằm trong display_name
        if "build_number" in metadata and "build" not in current_display.lower():
            build_number = metadata["build_number"]
            if f"build {build_number}" not in current_display.lower():
                metadata["display_name"] += f" (Build {build_number})"
    
    return metadata


# Đảm bảo thông tin phiên bản được khởi tạo khi module được import
initialize_version_info()