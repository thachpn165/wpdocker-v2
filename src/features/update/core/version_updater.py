"""
Trình cập nhật phiên bản đơn giản cho người dùng cuối.

Module này cung cấp một trình cập nhật đơn giản nhằm kiểm tra và cài đặt
các phiên bản mới của ứng dụng dành cho người dùng cuối, tập trung vào
tính đơn giản và dễ sử dụng.
"""

import os
import json
import re
import time
import shutil
import zipfile
import subprocess
from typing import Dict, Any, Optional

import requests
import semver
from tqdm import tqdm

from src.common.logging import Debug, log_call, debug, info, warn, error, success
from src.common.utils.environment import env


class VersionUpdater:
    """
    Trình cập nhật phiên bản đơn giản cho người dùng cuối.
    
    Lớp này cung cấp các chức năng để kiểm tra, tải xuống và cài đặt
    các bản cập nhật từ GitHub Releases.
    """
    
    def __init__(self):
        """Khởi tạo trình cập nhật phiên bản."""
        self.debug = Debug("VersionUpdater")

        # Lấy URL repo từ biến môi trường CORE_REPO
        self.core_repo = env.get("CORE_REPO", "https://github.com/thachpn165/wpdocker-v2")

        # Chuyển đổi từ định dạng GitHub URL thông thường sang API URL
        # Ví dụ: https://github.com/username/repo -> https://api.github.com/repos/username/repo
        if "github.com" in self.core_repo:
            repo_path = self.core_repo.replace("https://github.com/", "")
            # Sử dụng /releases thay vì /releases/latest để linh hoạt hơn
            self.api_url = f"https://api.github.com/repos/{repo_path}/releases"
            # URL cho việc kiểm tra tags nếu không có releases
            self.tags_url = f"https://api.github.com/repos/{repo_path}/tags"
            # URL trực tiếp để tải file từ GitHub
            self.raw_content_url = f"https://raw.githubusercontent.com/{repo_path}"
        else:
            # Fallback nếu URL không đúng định dạng
            self.debug.warn(f"Không thể chuyển đổi {self.core_repo} thành GitHub API URL. Sử dụng giá trị mặc định.")
            repo_path = "thachpn165/wpdocker-v2"
            self.api_url = f"https://api.github.com/repos/{repo_path}/releases"
            self.tags_url = f"https://api.github.com/repos/{repo_path}/tags"
            self.raw_content_url = f"https://raw.githubusercontent.com/{repo_path}"

        self.temp_dir = os.path.join(env.get("TEMP_DIR", "/tmp"), "wpdocker_update")
        self.cache_dir = env.get("CACHE_DIR", "/tmp")

    @log_call
    def _get_newest_asset(self, assets: list, prefer_name: str = None) -> Optional[dict]:
        """
        Lấy asset mới nhất từ danh sách assets, ưu tiên theo tên nếu được chỉ định.

        Args:
            assets: Danh sách các asset
            prefer_name: Tên file ưu tiên (nếu có, ví dụ wpdocker-nightly-latest.zip)

        Returns:
            Asset mới nhất hoặc None nếu không có asset nào
        """
        if not assets:
            self.debug.info("Không có assets nào để lựa chọn")
            return None

        # Lọc ra các assets là file zip
        zip_assets = [a for a in assets if a.get("name", "").endswith(".zip")]
        if not zip_assets:
            self.debug.info("Không tìm thấy file zip nào trong danh sách assets")
            return None

        self.debug.info(f"Tìm thấy {len(zip_assets)} file zip trong release này")

        # Ưu tiên file có tên chỉ định (như wpdocker-nightly-latest.zip)
        if prefer_name:
            preferred_assets = [a for a in zip_assets if a.get("name") == prefer_name]
            if preferred_assets:
                self.debug.info(f"Đã tìm thấy file ưu tiên: {prefer_name}")

                # Kiểm tra xem file ưu tiên có quá cũ không (quá 48 giờ)
                preferred_time = preferred_assets[0].get("created_at", "")
                if preferred_time:
                    try:
                        from datetime import datetime, timedelta
                        created_time = datetime.strptime(preferred_time, "%Y-%m-%dT%H:%M:%SZ")
                        now = datetime.utcnow()

                        # Nếu file được tạo trong vòng 48 giờ, sử dụng nó
                        if now - created_time < timedelta(hours=48):
                            self.debug.info(f"File {prefer_name} được tạo gần đây ({preferred_time}), sử dụng nó")
                            return preferred_assets[0]
                        else:
                            self.debug.info(f"File {prefer_name} quá cũ (tạo lúc: {preferred_time}), tìm file mới hơn")
                    except Exception as e:
                        self.debug.warn(f"Lỗi phân tích thời gian tạo: {str(e)}")
                else:
                    # Nếu không có thông tin thời gian, vẫn sử dụng file ưu tiên
                    return preferred_assets[0]

        # Sắp xếp assets theo thời gian tạo, mới nhất lên đầu
        try:
            # In ra thông tin debug để kiểm tra
            for asset in zip_assets:
                self.debug.debug(f"Asset: {asset.get('name')}, tạo lúc: {asset.get('created_at')}")

            sorted_assets = sorted(
                zip_assets,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

            # Ưu tiên những file có 'nightly' trong tên nếu đang ở kênh nightly
            user_channel = self._get_user_channel()
            if user_channel == "nightly":
                nightly_assets = [a for a in sorted_assets if "nightly" in a.get("name", "").lower()]
                if nightly_assets:
                    newest_asset = nightly_assets[0]
                    self.debug.info(f"Đã chọn file nightly mới nhất: {newest_asset.get('name')} (tạo lúc: {newest_asset.get('created_at')})")
                    return newest_asset

            newest_asset = sorted_assets[0]
            self.debug.info(f"Đã chọn file zip mới nhất: {newest_asset.get('name')} (tạo lúc: {newest_asset.get('created_at')})")
            return newest_asset

        except Exception as e:
            self.debug.error(f"Lỗi khi sắp xếp assets theo thời gian: {str(e)}")
            # Fallback: trả về asset đầu tiên nếu có lỗi khi sắp xếp
            if zip_assets:
                self.debug.info(f"Sử dụng asset đầu tiên trong danh sách do lỗi sắp xếp: {zip_assets[0].get('name')}")
                return zip_assets[0]
            return None

    @log_call
    def _get_user_channel(self) -> str:
        """
        Lấy kênh phát hành từ cấu hình người dùng.

        Returns:
            Kênh phát hành ("stable", "nightly", "dev") hoặc kênh mặc định từ version.py
        """
        try:
            from src.common.config.manager import ConfigManager
            from src.version import CHANNEL as DEFAULT_CHANNEL

            config = ConfigManager()
            user_channel = config.get("core.channel")

            if user_channel in ["stable", "nightly", "dev"]:
                self.debug.info(f"Sử dụng kênh từ config.json: {user_channel}")
                return user_channel

            self.debug.info(f"Không tìm thấy cấu hình core.channel, sử dụng kênh mặc định: {DEFAULT_CHANNEL}")
            return DEFAULT_CHANNEL
        except Exception as e:
            self.debug.warn(f"Lỗi khi đọc kênh phát hành từ config.json: {str(e)}")
            # Fallback to default channel in version.py
            from src.version import CHANNEL
            return CHANNEL
            
    @log_call
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        So sánh hai chuỗi phiên bản, hỗ trợ cả phiên bản semver và nightly.

        Args:
            version1: Phiên bản thứ nhất
            version2: Phiên bản thứ hai

        Returns:
            -1 nếu version1 < version2
             0 nếu version1 == version2
             1 nếu version1 > version2
        """
        try:
            # Kiểm tra nếu là phiên bản nightly
            is_nightly1 = "nightly" in version1.lower()
            is_nightly2 = "nightly" in version2.lower()

            # Nếu cả hai là phiên bản nightly
            if is_nightly1 and is_nightly2:
                # Trích xuất ngày từ chuỗi nightly (nightly-YYYYMMDD)
                date1 = re.search(r'(\d{8})', version1)
                date2 = re.search(r'(\d{8})', version2)

                # Nếu tìm thấy ngày trong cả hai chuỗi
                if date1 and date2:
                    date1 = date1.group(1)
                    date2 = date2.group(1)
                    return -1 if date1 < date2 else (1 if date1 > date2 else 0)

            # Nếu chỉ một trong hai là nightly
            if is_nightly1 and not is_nightly2:
                # Phiên bản nightly luôn mới hơn phiên bản stable
                return 1
            if not is_nightly1 and is_nightly2:
                # Phiên bản nightly luôn mới hơn phiên bản stable
                return -1

            # Sử dụng semver cho các trường hợp còn lại nếu cả hai phiên bản đều hợp lệ
            if self._is_valid_semver(version1) and self._is_valid_semver(version2):
                return semver.compare(version1, version2)
            else:
                # Sử dụng phương pháp so sánh thô sơ cho các phiên bản không tuân theo SemVer
                self.debug.info(f"Sử dụng so sánh thô sơ cho phiên bản không hợp lệ: {version1} vs {version2}")
                return self._simple_version_compare(version1, version2)
        except Exception as e:
            self.debug.warn(f"Lỗi khi so sánh phiên bản {version1} với {version2}: {str(e)}")

            # Phương pháp so sánh thô sơ khi không thể sử dụng semver
            return self._simple_version_compare(version1, version2)

    @log_call
    def _is_valid_semver(self, version: str) -> bool:
        """
        Kiểm tra xem một chuỗi phiên bản có tuân theo SemVer không.

        Args:
            version: Chuỗi phiên bản cần kiểm tra

        Returns:
            True nếu phiên bản hợp lệ theo SemVer, False nếu không
        """
        try:
            # Bỏ tiền tố 'v' nếu có
            if version.startswith('v'):
                version = version[1:]

            # Cố gắng phân tích chuỗi phiên bản
            semver.parse(version)
            return True
        except Exception:
            return False

    @log_call
    def _simple_version_compare(self, version1: str, version2: str) -> int:
        """
        So sánh phiên bản theo cách đơn giản khi không thể sử dụng semver.

        Args:
            version1: Phiên bản thứ nhất
            version2: Phiên bản thứ hai

        Returns:
            -1 nếu version1 < version2
             0 nếu version1 == version2
             1 nếu version1 > version2
        """
        # Tách các phần của phiên bản và so sánh từng phần
        parts1 = self._parse_version_parts(version1)
        parts2 = self._parse_version_parts(version2)

        # So sánh từng phần
        for i in range(min(len(parts1), len(parts2))):
            if parts1[i] < parts2[i]:
                return -1
            if parts1[i] > parts2[i]:
                return 1

        # Nếu tất cả các phần giống nhau, phiên bản có nhiều phần hơn được coi là mới hơn
        return -1 if len(parts1) < len(parts2) else (1 if len(parts1) > len(parts2) else 0)

    @log_call
    def _parse_version_parts(self, version: str) -> list:
        """
        Phân tích chuỗi phiên bản thành các phần.

        Args:
            version: Chuỗi phiên bản cần phân tích

        Returns:
            Danh sách các phần của phiên bản
        """
        # Loại bỏ các tiền tố phổ biến
        if version.startswith('v'):
            version = version[1:]

        # Phân tích phiên bản
        parts = []
        for part in version.split('.'):
            try:
                # Cố gắng chuyển đổi thành số
                parts.append(int(part))
            except ValueError:
                # Nếu không phải số, giữ nguyên dưới dạng chuỗi
                parts.append(part)

        return parts

    @log_call
    def check_for_updates(self, with_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Kiểm tra xem có phiên bản mới không.

        Args:
            with_cache: Sử dụng cache hay không

        Returns:
            Thông tin bản cập nhật hoặc None nếu không có
        """
        from src.version import VERSION

        # Lấy kênh phát hành từ config.json
        user_channel = self._get_user_channel()

        # Nếu người dùng đang sử dụng kênh dev, không kiểm tra cập nhật
        if user_channel == "dev":
            self.debug.info("Kênh Dev không hỗ trợ cập nhật tự động")
            return None

        # Sử dụng cache nếu được yêu cầu
        if with_cache:
            cache_file = os.path.join(self.cache_dir, "update_check.json")
            if os.path.exists(cache_file):
                # Cache có hiệu lực trong 24 giờ
                if time.time() - os.path.getmtime(cache_file) < 24 * 60 * 60:
                    try:
                        with open(cache_file, 'r') as f:
                            cached_data = json.load(f)
                            self.debug.info(f"Sử dụng dữ liệu cập nhật từ cache")
                            return cached_data
                    except Exception as e:
                        self.debug.warn(f"Lỗi đọc cache: {str(e)}")

        try:
            # Thêm token GitHub nếu có (để tăng giới hạn API)
            headers = {"Accept": "application/vnd.github.v3+json"}
            github_token = env.get("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"

            # Phương án 1: Thử kiểm tra releases
            self.debug.info(f"Kiểm tra bản cập nhật mới từ releases: {self.api_url}")
            response = requests.get(
                self.api_url,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                releases = response.json()

                # Nếu có releases
                if releases and isinstance(releases, list) and len(releases) > 0:
                    latest_release = None

                    if user_channel == "nightly":
                        # Nếu người dùng sử dụng kênh nightly, tìm pre-release đầu tiên
                        self.debug.info("Đang sử dụng kênh nightly, tìm kiếm pre-release...")
                        prerelease = next((r for r in releases if r.get("prerelease", True)), None)
                        if prerelease:
                            latest_release = prerelease
                            self.debug.info("Tìm thấy pre-release phù hợp với kênh nightly")

                    # Nếu không tìm thấy pre-release hoặc không phải kênh nightly, sử dụng release đầu tiên
                    if not latest_release:
                        if user_channel == "nightly":
                            self.debug.info("Không tìm thấy pre-release, sử dụng release mới nhất")
                        else:
                            self.debug.info("Đang sử dụng kênh stable, tìm kiếm release...")
                        latest_release = releases[0]  # Lấy release mới nhất

                    tag_name = latest_release.get("tag_name", "")

                    if tag_name:
                        latest_version = tag_name.lstrip("v")
                        is_nightly = "nightly" in tag_name.lower() or "pre" in tag_name.lower() or latest_release.get("prerelease", False)
                        release_channel = "nightly" if is_nightly else "stable"

                        # Kiểm tra xem phiên bản có phù hợp với kênh người dùng không
                        if user_channel == "stable" and release_channel == "nightly":
                            self.debug.info(f"Bỏ qua phiên bản nightly {latest_version} vì người dùng đang sử dụng kênh stable")
                            # Tiếp tục kiểm tra phương án khác nếu đang ở kênh stable nhưng tìm thấy bản nightly
                        else:
                            # So sánh phiên bản
                            try:
                                if self._compare_versions(latest_version, VERSION) > 0:
                                    # Tìm tệp tin cần tải xuống
                                    assets = latest_release.get("assets", [])
                                    if assets:
                                        # Ưu tiên tìm file có tên chỉ định cho kênh
                                        preferred_filename = None
                                        if is_nightly or "nightly" in tag_name.lower():
                                            preferred_filename = "wpdocker-nightly-latest.zip"
                                            self.debug.info(f"Đang tìm kiếm file nightly với tên: {preferred_filename}")
                                        elif user_channel == "stable":
                                            preferred_filename = f"wpdocker-v2-{latest_version}.zip"
                                            self.debug.info(f"Đang tìm kiếm file stable với tên: {preferred_filename}")

                                        # Tìm asset mới nhất
                                        self.debug.info(f"Đang quét {len(assets)} assets để tìm file phù hợp nhất...")
                                        asset = self._get_newest_asset(assets, preferred_filename)
                                        if asset:
                                            download_url = asset.get("browser_download_url")

                                            if download_url:
                                                # Chuẩn bị kết quả
                                                result = {
                                                    "version": latest_version,
                                                    "url": download_url,
                                                    "release_notes": latest_release.get("body", ""),
                                                    "published_at": latest_release.get("published_at", ""),
                                                    "channel": release_channel
                                                }

                                                self.debug.info(f"Tìm thấy phiên bản mới: {latest_version} ({release_channel})")

                                                # Cập nhật cache
                                                try:
                                                    cache_file = os.path.join(self.cache_dir, "update_check.json")
                                                    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                                                    with open(cache_file, 'w') as f:
                                                        json.dump(result, f)
                                                        self.debug.debug(f"Đã cập nhật cache: {cache_file}")
                                                except Exception as e:
                                                    self.debug.warn(f"Lỗi cập nhật cache: {str(e)}")

                                                return result
                            except Exception as e:
                                self.debug.error(f"Lỗi so sánh phiên bản từ releases: {str(e)}")

            # Phương án 2: Kiểm tra tags nếu không có releases hoặc releases không hoạt động
            self.debug.info(f"Kiểm tra bản cập nhật mới từ tags: {self.tags_url}")
            response = requests.get(
                self.tags_url,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                tags = response.json()

                # Nếu có tags
                if tags and isinstance(tags, list) and len(tags) > 0:
                    latest_tag = tags[0]  # Lấy tag mới nhất
                    tag_name = latest_tag.get("name", "")

                    if tag_name:
                        latest_version = tag_name.lstrip("v")
                        is_nightly = "nightly" in tag_name.lower() or "pre" in tag_name.lower()
                        tag_channel = "nightly" if is_nightly else "stable"

                        # Kiểm tra xem phiên bản có phù hợp với kênh người dùng không
                        if user_channel == "stable" and tag_channel == "nightly":
                            self.debug.info(f"Bỏ qua phiên bản nightly {latest_version} vì người dùng đang sử dụng kênh stable")
                        else:
                            # So sánh phiên bản
                            try:
                                if self._compare_versions(latest_version, VERSION) > 0:
                                    # Trong trường hợp sử dụng tag, chúng ta có thể tải source code dưới dạng .zip
                                    download_url = f"{self.core_repo}/archive/refs/tags/{tag_name}.zip"
                                    self.debug.info(f"Sử dụng URL tải xuống trực tiếp từ tag: {download_url}")

                                    # Chuẩn bị kết quả
                                    result = {
                                        "version": latest_version,
                                        "url": download_url,
                                        "release_notes": f"Cập nhật từ tag: {tag_name}",
                                        "published_at": "",
                                        "channel": tag_channel
                                    }

                                    self.debug.info(f"Tìm thấy phiên bản mới từ tag: {latest_version} ({tag_channel})")

                                    # Cập nhật cache
                                    try:
                                        cache_file = os.path.join(self.cache_dir, "update_check.json")
                                        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                                        with open(cache_file, 'w') as f:
                                            json.dump(result, f)
                                            self.debug.debug(f"Đã cập nhật cache: {cache_file}")
                                    except Exception as e:
                                        self.debug.warn(f"Lỗi cập nhật cache: {str(e)}")

                                    return result
                            except Exception as e:
                                self.debug.error(f"Lỗi so sánh phiên bản từ tags: {str(e)}")

            # Phương án 3: Kiểm tra trực tiếp file version.py dựa vào kênh người dùng
            self.debug.info(f"Kiểm tra phiên bản từ version.py trên repo (kênh người dùng hiện tại: {user_channel})")

            # Xác định các nhánh sẽ kiểm tra dựa trên kênh người dùng
            branches_to_check = []
            if user_channel == "stable":
                branches_to_check = ["main", "master"]
            elif user_channel == "nightly":
                branches_to_check = ["dev", "main", "master"]
            else:  # Các kênh khác
                branches_to_check = ["dev", "main", "master"]

            self.debug.info(f"Sẽ kiểm tra các nhánh: {', '.join(branches_to_check)}")

            for branch in branches_to_check:
                try:
                    version_url = f"{self.raw_content_url}/{branch}/src/version.py"
                    self.debug.info(f"Kiểm tra version.py tại: {version_url}")

                    response = requests.get(version_url, timeout=10)
                    if response.status_code == 200:
                        version_content = response.text

                        # Tìm version và channel trong nội dung file
                        version_match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', version_content)
                        channel_match = re.search(r'CHANNEL\s*=\s*["\']([^"\']+)["\']', version_content)

                        remote_version = None
                        remote_channel = None

                        if version_match:
                            remote_version = version_match.group(1)
                            if channel_match:
                                remote_channel = channel_match.group(1)
                            else:
                                remote_channel = "stable"  # Mặc định nếu không tìm thấy

                            self.debug.info(f"Phiên bản tìm thấy trong file version.py: {remote_version} (channel: {remote_channel})")

                            # Kiểm tra xem phiên bản có phù hợp với kênh người dùng không
                            if user_channel == "stable" and remote_channel == "nightly":
                                self.debug.info(f"Bỏ qua phiên bản nightly {remote_version} vì người dùng đang sử dụng kênh stable")
                                continue

                            # So sánh phiên bản
                            try:
                                if self._compare_versions(remote_version, VERSION) > 0:
                                    # Tạo URL download cho zip của nhánh
                                    download_url = f"{self.core_repo}/archive/refs/heads/{branch}.zip"
                                    self.debug.info(f"Sử dụng URL tải xuống từ nhánh {branch}: {download_url}")

                                    # Chuẩn bị kết quả
                                    result = {
                                        "version": remote_version,
                                        "url": download_url,
                                        "release_notes": f"Cập nhật từ nhánh {branch}",
                                        "published_at": "",
                                        "channel": remote_channel
                                    }

                                    self.debug.info(f"Tìm thấy phiên bản mới từ nhánh {branch}: {remote_version} (channel: {remote_channel})")

                                    # Cập nhật cache
                                    try:
                                        cache_file = os.path.join(self.cache_dir, "update_check.json")
                                        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                                        with open(cache_file, 'w') as f:
                                            json.dump(result, f)
                                            self.debug.debug(f"Đã cập nhật cache: {cache_file}")
                                    except Exception as e:
                                        self.debug.warn(f"Lỗi cập nhật cache: {str(e)}")

                                    return result
                                else:
                                    self.debug.info(f"Phiên bản hiện tại {VERSION} là mới nhất so với {remote_version} trên nhánh {branch}")
                            except Exception as e:
                                self.debug.error(f"Lỗi so sánh phiên bản từ version.py: {str(e)}")
                        else:
                            self.debug.warn(f"Không tìm thấy định nghĩa VERSION trong file version.py")
                except Exception as e:
                    self.debug.warn(f"Lỗi khi kiểm tra version.py trên nhánh {branch}: {str(e)}")

            self.debug.info(f"Không tìm thấy bản cập nhật nào - phiên bản hiện tại: {VERSION}")
            return None

        except Exception as e:
            self.debug.error(f"Lỗi kiểm tra cập nhật: {str(e)}")
            return None
            
    @log_call
    def download_update(self, update_info: Dict[str, Any]) -> Optional[str]:
        """
        Tải xuống bản cập nhật.

        Args:
            update_info: Thông tin bản cập nhật từ check_for_updates()

        Returns:
            Đường dẫn đến file zip đã tải hoặc None nếu thất bại
        """
        try:
            # Tạo thư mục tạm thời
            os.makedirs(self.temp_dir, exist_ok=True)
            zip_path = os.path.join(self.temp_dir, "update.zip")
            self.debug.info(f"Đang tải bản cập nhật từ {update_info['url']}")

            # Tải xuống bản cập nhật
            try:
                response = requests.get(update_info["url"], stream=True, timeout=60)
                if response.status_code != 200:
                    self.debug.error(f"Lỗi tải xuống: {response.status_code}, Response: {response.text[:200]}")
                    return None
            except requests.exceptions.RequestException as req_err:
                self.debug.error(f"Lỗi kết nối khi tải xuống: {str(req_err)}")
                return None

            # Hiển thị tiến trình tải xuống
            total_size = int(response.headers.get('content-length', 0))
            self.debug.info(f"Kích thước file cần tải: {total_size/1024/1024:.2f} MB")
            progress = tqdm(total=total_size, unit='B', unit_scale=True)

            try:
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(len(chunk))

                progress.close()

                # Kiểm tra kích thước file đã tải
                actual_size = os.path.getsize(zip_path)
                self.debug.info(f"Đã tải xuống thành công: {zip_path} (kích thước: {actual_size/1024/1024:.2f} MB)")

                if total_size > 0 and abs(total_size - actual_size) > 1024:  # Nếu chênh lệch hơn 1KB
                    self.debug.warn(f"Kích thước file không khớp: Cần {total_size} bytes, thực tế {actual_size} bytes")

            except IOError as io_err:
                self.debug.error(f"Lỗi ghi file: {str(io_err)}")
                return None

            # Kiểm tra tệp tin đã tải
            if not os.path.exists(zip_path):
                self.debug.error("Tệp tin tải xuống không tồn tại")
                return None

            if os.path.getsize(zip_path) == 0:
                self.debug.error("Tệp tin tải xuống có kích thước 0 bytes")
                return None

            # Kiểm tra nhanh xem file zip có hợp lệ không
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_check:
                    # Đọc thông tin file để xác minh tính hợp lệ
                    file_list = zip_check.namelist()
                    self.debug.info(f"File zip hợp lệ, chứa {len(file_list)} files/thư mục")
            except zipfile.BadZipFile:
                self.debug.error("File tải xuống không phải là file ZIP hợp lệ")
                return None

            return zip_path

        except Exception as e:
            self.debug.error(f"Lỗi tải xuống bản cập nhật: {str(e)}")
            import traceback
            self.debug.error(traceback.format_exc())
            return None
            
    @log_call
    def _backup_current_installation(self, backup_dir: str) -> bool:
        """
        Sao lưu cài đặt hiện tại.
        
        Args:
            backup_dir: Thư mục sao lưu
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Xác định thư mục cài đặt
            install_dir = env.get("INSTALL_DIR")
            if not install_dir:
                # Mặc định sử dụng thư mục hiện tại
                install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # Tạo thư mục sao lưu
            os.makedirs(backup_dir, exist_ok=True)
            self.debug.info(f"Đang sao lưu cài đặt hiện tại vào {backup_dir}")
            
            # Sao lưu các thư mục quan trọng
            dirs_to_backup = ["src", "templates", "scripts"]
            for dir_name in dirs_to_backup:
                src_path = os.path.join(install_dir, dir_name)
                if os.path.exists(src_path):
                    dest_path = os.path.join(backup_dir, dir_name)
                    shutil.copytree(src_path, dest_path)
                    self.debug.debug(f"Đã sao lưu {dir_name}")
            
            # Sao lưu các tệp tin cấu hình
            files_to_backup = ["requirements.txt"]
            for file_name in files_to_backup:
                file_path = os.path.join(install_dir, file_name)
                if os.path.exists(file_path):
                    shutil.copy2(file_path, os.path.join(backup_dir, file_name))
                    self.debug.debug(f"Đã sao lưu {file_name}")
                    
            return True
            
        except Exception as e:
            self.debug.error(f"Lỗi sao lưu cài đặt: {str(e)}")
            return False
            
    @log_call
    def _restore_from_backup(self, backup_dir: str) -> bool:
        """
        Khôi phục từ bản sao lưu.
        
        Args:
            backup_dir: Thư mục sao lưu
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Xác định thư mục cài đặt
            install_dir = env.get("INSTALL_DIR")
            if not install_dir:
                # Mặc định sử dụng thư mục hiện tại
                install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            self.debug.info(f"Đang khôi phục từ bản sao lưu {backup_dir}")
            
            # Khôi phục các thư mục
            dirs_to_restore = ["src", "templates", "scripts"]
            for dir_name in dirs_to_restore:
                backup_path = os.path.join(backup_dir, dir_name)
                if os.path.exists(backup_path):
                    dest_path = os.path.join(install_dir, dir_name)
                    # Xóa thư mục hiện tại nếu tồn tại
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    # Khôi phục từ bản sao lưu
                    shutil.copytree(backup_path, dest_path)
                    self.debug.debug(f"Đã khôi phục {dir_name}")
            
            # Khôi phục các tệp tin cấu hình
            files_to_restore = ["requirements.txt"]
            for file_name in files_to_restore:
                backup_file = os.path.join(backup_dir, file_name)
                if os.path.exists(backup_file):
                    shutil.copy2(backup_file, os.path.join(install_dir, file_name))
                    self.debug.debug(f"Đã khôi phục {file_name}")
                    
            return True
            
        except Exception as e:
            self.debug.error(f"Lỗi khôi phục từ bản sao lưu: {str(e)}")
            return False
            
    @log_call
    def _install_update(self, zip_path: str) -> bool:
        """
        Cài đặt bản cập nhật từ file zip đã tải.

        Args:
            zip_path: Đường dẫn đến file zip

        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Xác định thư mục cài đặt
            install_dir = env.get("INSTALL_DIR")
            if not install_dir:
                # Mặc định sử dụng thư mục hiện tại
                install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

            self.debug.info(f"Thư mục cài đặt: {install_dir}")

            # Thư mục giải nén tạm thời
            extract_dir = os.path.join(self.temp_dir, "extracted")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)  # Xóa nếu đã tồn tại
            os.makedirs(extract_dir, exist_ok=True)

            # Giải nén bản cập nhật
            self.debug.info(f"Đang giải nén bản cập nhật vào {extract_dir}")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Kiểm tra danh sách file trước khi giải nén
                    file_list = zip_ref.namelist()
                    self.debug.info(f"File zip chứa {len(file_list)} files/thư mục")

                    # Hiển thị một số thư mục chính
                    root_dirs = set()
                    for f in file_list:
                        parts = f.split('/')
                        if len(parts) > 0:
                            root_dirs.add(parts[0])

                    self.debug.info(f"Các thư mục gốc trong file zip: {', '.join(root_dirs)}")

                    # Giải nén
                    zip_ref.extractall(extract_dir)
                    self.debug.info("Đã giải nén thành công")
            except zipfile.BadZipFile:
                self.debug.error("File ZIP không hợp lệ")
                return False
            except Exception as e:
                self.debug.error(f"Lỗi khi giải nén: {str(e)}")
                return False

            # Cài đặt bản cập nhật
            self.debug.info(f"Đang cài đặt bản cập nhật vào {install_dir}")

            # Kiểm tra xem có nhiều thư mục con hay không
            # Một số file zip từ GitHub có thể có thư mục cha bọc ngoài
            items = os.listdir(extract_dir)
            if len(items) == 1 and os.path.isdir(os.path.join(extract_dir, items[0])):
                # Nếu chỉ có một thư mục và nó chứa các thư mục src, templates, etc.
                # thì sử dụng thư mục đó làm thư mục gốc
                potential_root = os.path.join(extract_dir, items[0])
                if os.path.exists(os.path.join(potential_root, "src")):
                    self.debug.info(f"Đã phát hiện thư mục gốc: {items[0]}")
                    extract_dir = potential_root

            updated = False

            # Kiểm tra xem có thư mục src trong bản giải nén không
            src_dir = os.path.join(extract_dir, "src")
            if os.path.exists(src_dir) and os.path.isdir(src_dir):
                # Kiểm tra nhanh xem có phải thư mục src hợp lệ không
                if os.path.exists(os.path.join(src_dir, "main.py")) or \
                   os.path.exists(os.path.join(src_dir, "version.py")) or \
                   os.path.exists(os.path.join(src_dir, "features")):
                    # Cập nhật thư mục src
                    dest_src_dir = os.path.join(install_dir, "src")
                    if os.path.exists(dest_src_dir):
                        shutil.rmtree(dest_src_dir)
                    shutil.copytree(src_dir, dest_src_dir)
                    self.debug.info("Đã cập nhật thư mục src")
                    updated = True
                else:
                    self.debug.warn("Phát hiện thư mục src nhưng không có cấu trúc chuẩn")

            # Kiểm tra và cập nhật thư mục templates nếu có
            templates_dir = os.path.join(extract_dir, "templates")
            if os.path.exists(templates_dir) and os.path.isdir(templates_dir):
                dest_templates_dir = os.path.join(install_dir, "templates")
                if os.path.exists(dest_templates_dir):
                    shutil.rmtree(dest_templates_dir)
                shutil.copytree(templates_dir, dest_templates_dir)
                self.debug.info("Đã cập nhật thư mục templates")
                updated = True

            # Cập nhật thư mục scripts nếu có
            scripts_dir = os.path.join(extract_dir, "scripts")
            if os.path.exists(scripts_dir) and os.path.isdir(scripts_dir):
                dest_scripts_dir = os.path.join(install_dir, "scripts")
                if os.path.exists(dest_scripts_dir):
                    shutil.rmtree(dest_scripts_dir)
                shutil.copytree(scripts_dir, dest_scripts_dir)
                self.debug.info("Đã cập nhật thư mục scripts")
                updated = True

            # Cập nhật requirements.txt nếu có
            req_file = os.path.join(extract_dir, "requirements.txt")
            if os.path.exists(req_file):
                shutil.copy2(req_file, os.path.join(install_dir, "requirements.txt"))
                self.debug.info("Đã cập nhật requirements.txt")
                updated = True

            # Kiểm tra xem có bất kỳ thành phần nào được cập nhật không
            if not updated:
                self.debug.error("Không tìm thấy thư mục/tệp tin cần cập nhật trong bản giải nén")
                return False

            return True

        except Exception as e:
            self.debug.error(f"Lỗi cài đặt bản cập nhật: {str(e)}")
            import traceback
            self.debug.error(traceback.format_exc())
            return False
            
    @log_call
    def _update_dependencies(self) -> bool:
        """
        Cập nhật các dependencies.
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Xác định thư mục cài đặt
            install_dir = env.get("INSTALL_DIR")
            if not install_dir:
                # Mặc định sử dụng thư mục hiện tại
                install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # Kiểm tra xem requirements.txt có tồn tại không
            req_file = os.path.join(install_dir, "requirements.txt")
            if not os.path.exists(req_file):
                self.debug.warn("Không tìm thấy requirements.txt")
                return False
                
            # Cập nhật dependencies
            self.debug.info("Đang cập nhật dependencies")
            result = subprocess.run(
                ["pip", "install", "-r", req_file],
                cwd=install_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.debug.error(f"Lỗi cập nhật dependencies: {result.stderr}")
                return False
                
            self.debug.info("Đã cập nhật dependencies thành công")
            return True
            
        except Exception as e:
            self.debug.error(f"Lỗi cập nhật dependencies: {str(e)}")
            return False
            
    @log_call
    def download_and_install(self, update_info: Dict[str, Any]) -> bool:
        """
        Tải xuống và cài đặt bản cập nhật.
        
        Args:
            update_info: Thông tin bản cập nhật từ check_for_updates()
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Tạo thư mục tạm thời nếu chưa tồn tại
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # Tải xuống bản cập nhật
            self.debug.info("Bắt đầu tải xuống bản cập nhật...")
            zip_path = self.download_update(update_info)
            if not zip_path:
                return False
                
            # Sao lưu cài đặt hiện tại
            backup_dir = os.path.join(self.temp_dir, "backup")
            self.debug.info("Đang sao lưu cài đặt hiện tại...")
            if not self._backup_current_installation(backup_dir):
                self.debug.error("Không thể sao lưu cài đặt hiện tại")
                return False
                
            # Cài đặt bản cập nhật
            self.debug.info("Đang cài đặt bản cập nhật...")
            success = self._install_update(zip_path)
            
            if not success:
                # Khôi phục từ bản sao lưu nếu cài đặt thất bại
                self.debug.warn("Cài đặt thất bại, đang khôi phục...")
                self._restore_from_backup(backup_dir)
                return False
                
            # Cập nhật dependencies nếu cần
            self.debug.info("Đang cập nhật dependencies...")
            self._update_dependencies()
            
            # Dọn dẹp
            try:
                shutil.rmtree(self.temp_dir)
                self.debug.info(f"Đã dọn dẹp thư mục tạm thời: {self.temp_dir}")
            except Exception as e:
                self.debug.warn(f"Lỗi dọn dẹp: {str(e)}")
                
            success(f"Đã cập nhật thành công lên phiên bản {update_info['version']}")
            return True
            
        except Exception as e:
            self.debug.error(f"Lỗi cài đặt bản cập nhật: {str(e)}")
            return False
            
    @log_call
    def prompt_update(self) -> bool:
        """
        Hiển thị thông báo cập nhật cho người dùng.
        
        Returns:
            True nếu người dùng chọn cập nhật và cập nhật thành công,
            False nếu không có bản cập nhật, người dùng từ chối hoặc cập nhật thất bại
        """
        # Kiểm tra cập nhật
        update_info = self.check_for_updates()
        if not update_info:
            info("Bạn đang sử dụng phiên bản mới nhất.")
            return False
            
        # Hiển thị thông tin cập nhật
        info("┌───────────────────────────────────────────┐")
        info(f"│         Có bản cập nhật mới!              │")
        info(f"│ Phiên bản: {update_info['version']} (kênh: {update_info.get('channel', 'stable')}) │")
        info("└───────────────────────────────────────────┘")
        
        # Hiển thị ghi chú phát hành nếu có
        if update_info["release_notes"]:
            info("Nội dung cập nhật:")
            notes = update_info["release_notes"]
            # Hiển thị tối đa 500 ký tự
            if len(notes) > 500:
                notes = notes[:500] + "..."
            info(notes)
            
        # Hỏi người dùng có muốn cập nhật không
        from src.common.ui.prompt_helpers import prompt_yes_no
        
        if prompt_yes_no("Bạn có muốn cài đặt bản cập nhật này ngay bây giờ không?"):
            success = self.download_and_install(update_info)
            if success:
                # Đảm bảo giữ nguyên kênh người dùng sau khi cập nhật
                try:
                    from src.common.config.manager import ConfigManager
                    config = ConfigManager()

                    # Đảm bảo thiết lập kênh được lưu trong config
                    current_channel = config.get("core.channel")
                    if current_channel in ["stable", "nightly", "dev"]:
                        self.debug.info(f"Giữ nguyên kênh người dùng sau cập nhật: {current_channel}")
                        config.set("core.channel", current_channel)
                except Exception as e:
                    self.debug.warn(f"Không thể cập nhật cấu hình kênh: {str(e)}")

                success("Cập nhật thành công! Vui lòng khởi động lại ứng dụng.")
                return True
            else:
                error("Cập nhật thất bại. Vui lòng thử lại sau.")
                return False
        else:
            info("Bạn có thể cập nhật sau bằng cách chọn 'Kiểm tra cập nhật' từ menu.")
            return False


# Singleton instance
version_updater = VersionUpdater()


@log_call
def check_for_updates(with_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Kiểm tra xem có phiên bản mới không.
    
    Args:
        with_cache: Sử dụng cache hay không
        
    Returns:
        Thông tin bản cập nhật hoặc None nếu không có
    """
    return version_updater.check_for_updates(with_cache)


@log_call
def download_and_install(update_info: Dict[str, Any]) -> bool:
    """
    Tải xuống và cài đặt bản cập nhật.
    
    Args:
        update_info: Thông tin bản cập nhật từ check_for_updates()
        
    Returns:
        True nếu thành công, False nếu thất bại
    """
    return version_updater.download_and_install(update_info)


@log_call
def prompt_update() -> bool:
    """
    Hiển thị thông báo cập nhật cho người dùng.
    
    Returns:
        True nếu người dùng chọn cập nhật và cập nhật thành công,
        False nếu không có bản cập nhật, người dùng từ chối hoặc cập nhật thất bại
    """
    return version_updater.prompt_update()