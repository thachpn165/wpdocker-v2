"""
Module for handling automated backup scheduling for websites.
"""
from questionary import select, confirm, text
import os
import time
from datetime import datetime
from dataclasses import asdict

from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.website_utils import select_website, get_site_config
from core.backend.models.config import BackupSchedule, CloudConfig, SiteBackup
from core.backend.modules.backup.backup_manager import BackupManager


class ScheduleBackupPrompt(PromptBase):
    """
    Class for handling automated backup scheduling prompt for websites.
    
    Implements the abstract PromptBase class with methods:
    - _collect_inputs: Collects information about the backup schedule
    - _process: Performs creation or update of the schedule
    - _show_results: Displays scheduling results
    """
    
    def _collect_inputs(self):
        """
        Thu thập thông tin về lịch trình backup từ người dùng.
        
        Returns:
            dict: Chứa thông tin cấu hình lịch trình hoặc None nếu bị hủy
        """
        # Chọn website để lên lịch backup
        domain = select_website("🌐 Chọn website để lên lịch backup tự động:")
        
        if not domain:
            # Thông báo lỗi đã được hiển thị trong hàm select_website
            return None
        
        # Khởi tạo BackupManager
        backup_manager = BackupManager()
        
        # Kiểm tra lịch trình hiện tại
        site_config = get_site_config(domain)
        has_existing_schedule = (site_config and site_config.backup and
                                site_config.backup.schedule and
                                site_config.backup.schedule.enabled)
        
        # Lấy danh sách storage providers
        storage_providers = backup_manager.get_available_providers()
        
        if not storage_providers:
            error("❌ Không tìm thấy nơi lưu trữ backup nào.")
            return None
        
        # Hành động dựa trên trạng thái hiện tại
        if has_existing_schedule:
            # Hiển thị thông tin lịch trình hiện tại
            current_schedule = site_config.backup.schedule
            current_cloud = site_config.backup.cloud_config
            
            info(f"⏰ Lịch trình backup hiện tại cho {domain}:")
            
            # Hiển thị tần suất
            schedule_type = current_schedule.schedule_type
            hour = current_schedule.hour
            minute = current_schedule.minute
            
            if schedule_type == "daily":
                info(f"  Hàng ngày lúc {hour:02d}:{minute:02d}")
            elif schedule_type == "weekly":
                day = current_schedule.day_of_week
                day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                day_name = day_names[day] if 0 <= day < len(day_names) else f"ngày {day}"
                info(f"  Hàng tuần vào {day_name} lúc {hour:02d}:{minute:02d}")
            elif schedule_type == "monthly":
                day = current_schedule.day_of_month
                info(f"  Hàng tháng vào ngày {day} lúc {hour:02d}:{minute:02d}")
            
            # Hiển thị số bản backup lưu giữ
            if current_schedule.retention_count:
                info(f"  Giữ lại {current_schedule.retention_count} bản backup gần nhất")
            
            # Hiển thị nơi lưu trữ
            if current_cloud and current_cloud.enabled:
                provider = current_cloud.provider
                remote = current_cloud.remote_name
                info(f"  Lưu trữ đám mây: {provider} ({remote})")
            else:
                info("  Lưu trữ: local")
            
            # Hỏi người dùng muốn làm gì với lịch trình
            action = select(
                "🔍 Bạn muốn làm gì với lịch trình backup hiện tại?",
                choices=[
                    "Chỉnh sửa lịch trình",
                    "Vô hiệu hóa lịch trình",
                    "Quay lại"
                ]
            ).ask()
            
            if not action or action == "Quay lại":
                info("Đã huỷ thao tác.")
                return None
            
            if action == "Vô hiệu hóa lịch trình":
                return {
                    "domain": domain,
                    "action": "disable",
                    "config": None
                }
            
            # Mặc định provider là local nếu không có cấu hình cloud hoặc cloud bị tắt
            provider = "local"
            if current_cloud and current_cloud.enabled and current_cloud.remote_name:
                provider = f"rclone:{current_cloud.remote_name}"
            
            # Nếu chọn cập nhật, tiếp tục với tuỳ chọn
            schedule_type_mapping = {
                "daily": "Hàng ngày",
                "weekly": "Hàng tuần",
                "monthly": "Hàng tháng"
            }
            
            # Chọn tần suất backup
            selected_schedule_type = select(
                "🔄 Chọn tần suất backup:",
                choices=["Hàng ngày", "Hàng tuần", "Hàng tháng"],
                default=schedule_type_mapping.get(schedule_type, "Hàng ngày")
            ).ask()
            
            if not selected_schedule_type:
                info("Đã huỷ thao tác.")
                return None
            
            # Chọn thời gian backup (giờ và phút)
            hour_choices = [f"{h:02d}" for h in range(24)]
            selected_hour = select(
                "🕒 Chọn giờ thực hiện backup (0-23):",
                choices=hour_choices,
                default=f"{hour:02d}"
            ).ask()
            
            if not selected_hour:
                info("Đã huỷ thao tác.")
                return None
            
            minute_choices = ["00", "15", "30", "45"]
            selected_minute = select(
                "🕒 Chọn phút (0, 15, 30, 45):",
                choices=minute_choices,
                default=f"{minute:02d}" if minute in [0, 15, 30, 45] else "00"
            ).ask()
            
            if not selected_minute:
                info("Đã huỷ thao tác.")
                return None
            
            # Chuyển đổi
            hour_int = int(selected_hour)
            minute_int = int(selected_minute)
            
            # Tuỳ chọn thêm dựa vào loại lịch
            day_of_week = None
            day_of_month = None
            
            if selected_schedule_type == "Hàng tuần":
                day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                default_day = day_names[current_schedule.day_of_week] if 0 <= current_schedule.day_of_week < len(day_names) else "Chủ Nhật"
                
                selected_day = select(
                    "📅 Chọn ngày trong tuần:",
                    choices=day_names,
                    default=default_day
                ).ask()
                
                if not selected_day:
                    info("Đã huỷ thao tác.")
                    return None
                
                day_map = {
                    "Thứ Hai": 0, "Thứ Ba": 1, "Thứ Tư": 2, "Thứ Năm": 3, 
                    "Thứ Sáu": 4, "Thứ Bảy": 5, "Chủ Nhật": 6
                }
                day_of_week = day_map.get(selected_day, 0)
            
            elif selected_schedule_type == "Hàng tháng":
                day_choices = [str(d) for d in range(1, 29)]  # 1-28 an toàn cho tất cả các tháng
                default_day = str(current_schedule.day_of_month) if 1 <= current_schedule.day_of_month <= 28 else "1"
                
                selected_day = select(
                    "📅 Chọn ngày trong tháng (1-28):",
                    choices=day_choices,
                    default=default_day
                ).ask()
                
                if not selected_day:
                    info("Đã huỷ thao tác.")
                    return None
                
                day_of_month = int(selected_day)
            
            # Số lượng backup giữ lại
            retention_text = text(
                "🗃️ Số lượng bản sao lưu gần nhất giữ lại (0 = giữ tất cả):",
                default=str(current_schedule.retention_count)
            ).ask()
            
            if not retention_text:
                retention_count = 3  # Giá trị mặc định
            else:
                try:
                    retention_count = int(retention_text)
                except ValueError:
                    retention_count = 3
                    warn("⚠️ Giá trị không hợp lệ, sử dụng giá trị mặc định: 3")
            
            # Format provider options to be more user-friendly
            provider_choices = []
            for prov in storage_providers:
                if prov == "local":
                    provider_choices.append({"name": "Lưu trữ local", "value": prov})
                elif prov.startswith("rclone:"):
                    remote_name = prov.split(":")[1]
                    provider_choices.append({"name": f"Lưu trữ đám mây ({remote_name})", "value": prov})
                else:
                    provider_choices.append({"name": prov, "value": prov})
            
            # Tìm provider mặc định
            default_provider = None
            for prov in provider_choices:
                if prov["value"] == provider:
                    default_provider = prov["name"]
                    break
            
            selected_provider = select(
                "💾 Chọn nơi lưu trữ backup:",
                choices=provider_choices,
                default=default_provider
            ).ask()
            
            if not selected_provider:
                info("Đã huỷ thao tác.")
                return None
            
            # Tạo schedule info để hiển thị trong xác nhận
            schedule_info = ""
            if selected_schedule_type == "Hàng ngày":
                schedule_info = f"hàng ngày lúc {hour_int:02d}:{minute_int:02d}"
            elif selected_schedule_type == "Hàng tuần":
                day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                day_name = day_names[day_of_week] if 0 <= day_of_week < len(day_names) else "Chủ Nhật"
                schedule_info = f"hàng tuần vào {day_name} lúc {hour_int:02d}:{minute_int:02d}"
            else:
                schedule_info = f"hàng tháng vào ngày {day_of_month} lúc {hour_int:02d}:{minute_int:02d}"
            
            # Format provider name cho đẹp
            provider_display = selected_provider
            if selected_provider == "local":
                provider_display = "lưu trữ local"
            elif selected_provider.startswith("rclone:"):
                remote_name = selected_provider.split(":")[1]
                provider_display = f"lưu trữ đám mây ({remote_name})"
            
            # Xác nhận
            if not confirm(f"⚠️ Xác nhận lịch trình {schedule_info} cho website {domain} tại {provider_display}?").ask():
                info("Đã huỷ thao tác.")
                return None
            
            # Tạo config
            config = {
                "enabled": True,
                "schedule_type": "daily" if selected_schedule_type == "Hàng ngày" else 
                              "weekly" if selected_schedule_type == "Hàng tuần" else 
                              "monthly",
                "hour": hour_int,
                "minute": minute_int,
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "retention_count": retention_count,
                "provider": selected_provider
            }
            
            return {
                "domain": domain,
                "action": "update",
                "config": config
            }
        else:
            # Không có lịch trình, hỏi người dùng có muốn tạo không
            if not confirm(f"⏰ Bạn muốn tạo lịch trình backup tự động cho website {domain}?").ask():
                info("Đã huỷ thao tác tạo lịch trình backup.")
                return None
            
            # Chọn tần suất backup
            schedule_type = select(
                "🔄 Chọn tần suất backup:",
                choices=["Hàng ngày", "Hàng tuần", "Hàng tháng"],
                default="Hàng ngày"
            ).ask()
            
            if not schedule_type:
                info("Đã huỷ thao tác.")
                return None
            
            # Chọn thời gian backup (giờ và phút)
            hour_choices = [f"{h:02d}" for h in range(24)]
            selected_hour = select(
                "🕒 Chọn giờ thực hiện backup (0-23):",
                choices=hour_choices,
                default="01"
            ).ask()
            
            if not selected_hour:
                info("Đã huỷ thao tác.")
                return None
            
            minute_choices = ["00", "15", "30", "45"]
            selected_minute = select(
                "🕒 Chọn phút (0, 15, 30, 45):",
                choices=minute_choices,
                default="00"
            ).ask()
            
            if not selected_minute:
                info("Đã huỷ thao tác.")
                return None
            
            # Chuyển đổi
            hour = int(selected_hour)
            minute = int(selected_minute)
            
            # Tuỳ chọn thêm dựa vào loại lịch
            day_of_week = None
            day_of_month = None
            
            if schedule_type == "Hàng tuần":
                selected_day = select(
                    "📅 Chọn ngày trong tuần:",
                    choices=["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"],
                    default="Chủ Nhật"
                ).ask()
                
                if not selected_day:
                    info("Đã huỷ thao tác.")
                    return None
                
                day_map = {
                    "Thứ Hai": 0, "Thứ Ba": 1, "Thứ Tư": 2, "Thứ Năm": 3, 
                    "Thứ Sáu": 4, "Thứ Bảy": 5, "Chủ Nhật": 6
                }
                day_of_week = day_map.get(selected_day, 0)
            
            elif schedule_type == "Hàng tháng":
                day_choices = [str(d) for d in range(1, 29)]  # 1-28 an toàn cho tất cả các tháng
                selected_day = select(
                    "📅 Chọn ngày trong tháng (1-28):",
                    choices=day_choices,
                    default="1"
                ).ask()
                
                if not selected_day:
                    info("Đã huỷ thao tác.")
                    return None
                
                day_of_month = int(selected_day)
            
            # Số lượng backup giữ lại
            retention_text = text(
                "🗃️ Số lượng bản sao lưu gần nhất giữ lại (0 = giữ tất cả):",
                default="3"
            ).ask()
            
            if not retention_text:
                retention_count = 3  # Giá trị mặc định
            else:
                try:
                    retention_count = int(retention_text)
                except ValueError:
                    retention_count = 3
                    warn("⚠️ Giá trị không hợp lệ, sử dụng giá trị mặc định: 3")
            
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
                choices=provider_choices,
                default="Lưu trữ local"
            ).ask()
            
            if not selected_provider:
                info("Đã huỷ thao tác.")
                return None
            
            # Tạo schedule info để hiển thị trong xác nhận
            schedule_info = ""
            if schedule_type == "Hàng ngày":
                schedule_info = f"hàng ngày lúc {hour:02d}:{minute:02d}"
            elif schedule_type == "Hàng tuần":
                day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                day_name = day_names[day_of_week] if 0 <= day_of_week < len(day_names) else "Chủ Nhật"
                schedule_info = f"hàng tuần vào {day_name} lúc {hour:02d}:{minute:02d}"
            else:
                schedule_info = f"hàng tháng vào ngày {day_of_month} lúc {hour:02d}:{minute:02d}"
            
            # Format provider name cho đẹp
            provider_display = selected_provider
            if selected_provider == "local":
                provider_display = "lưu trữ local"
            elif selected_provider.startswith("rclone:"):
                remote_name = selected_provider.split(":")[1]
                provider_display = f"lưu trữ đám mây ({remote_name})"
            
            # Xác nhận
            if not confirm(f"⚠️ Xác nhận tạo lịch trình backup {schedule_info} cho website {domain} tại {provider_display}?").ask():
                info("Đã huỷ thao tác.")
                return None
            
            # Tạo config
            config = {
                "enabled": True,
                "schedule_type": "daily" if schedule_type == "Hàng ngày" else 
                              "weekly" if schedule_type == "Hàng tuần" else 
                              "monthly",
                "hour": hour,
                "minute": minute,
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "retention_count": retention_count,
                "provider": selected_provider
            }
            
            return {
                "domain": domain,
                "action": "create",
                "config": config
            }
    
    def _process(self, inputs):
        """
        Xử lý việc tạo, cập nhật hoặc xóa lịch trình backup dựa trên thông tin đầu vào.
        
        Args:
            inputs: Dict chứa thông tin domain, hành động và cấu hình lịch trình
            
        Returns:
            dict: Kết quả xử lý
        """
        if not inputs:
            return None
            
        domain = inputs["domain"]
        action = inputs["action"]
        config = inputs.get("config")
        
        # Khởi tạo BackupManager
        backup_manager = BackupManager()
        
        result = {"success": False, "message": "", "domain": domain, "action": action}
        
        try:
            if action == "disable":
                # Vô hiệu hóa lịch trình
                schedule = {"enabled": False}
                success, message = backup_manager.schedule_backup(domain, schedule)
                
                result["success"] = success
                result["message"] = message
                
            elif action in ["create", "update"]:
                # Tạo/cập nhật lịch trình
                success, message = backup_manager.schedule_backup(domain, config, config["provider"])
                
                result["success"] = success
                result["message"] = message
                result["config"] = config
            
            return result
        except Exception as e:
            error_msg = f"Lỗi xử lý lịch trình backup: {str(e)}"
            error(error_msg)
            result["success"] = False
            result["message"] = error_msg
            return result
    
    def _show_results(self):
        """
        Hiển thị kết quả xử lý lịch trình backup.
        
        Sử dụng self.result để hiển thị kết quả xử lý.
        """
        if not self.result:
            return
            
        domain = self.result["domain"]
        action = self.result["action"]
        success = self.result["success"]
        message = self.result.get("message", "")
        config = self.result.get("config")
        
        if success:
            if action == "disable":
                success(f"✅ Đã vô hiệu hóa lịch trình backup cho website {domain}.")
            elif action == "create":
                success(f"✅ Đã tạo lịch trình backup cho website {domain}.")
                
                # Hiển thị thông tin lịch trình
                if config:
                    schedule_type = config["schedule_type"]
                    hour = config["hour"]
                    minute = config["minute"]
                    
                    schedule_info = ""
                    if schedule_type == "daily":
                        schedule_info = f"hàng ngày lúc {hour:02d}:{minute:02d}"
                    elif schedule_type == "weekly":
                        day = config["day_of_week"]
                        day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                        day_name = day_names[day] if 0 <= day < len(day_names) else f"ngày {day}"
                        schedule_info = f"hàng tuần vào {day_name} lúc {hour:02d}:{minute:02d}"
                    elif schedule_type == "monthly":
                        day = config["day_of_month"]
                        schedule_info = f"hàng tháng vào ngày {day} lúc {hour:02d}:{minute:02d}"
                    
                    # Hiển thị provider
                    provider = config["provider"]
                    provider_display = provider
                    if provider == "local":
                        provider_display = "lưu trữ local"
                    elif provider.startswith("rclone:"):
                        remote_name = provider.split(":")[1]
                        provider_display = f"lưu trữ đám mây ({remote_name})"
                    
                    info(f"⏰ Lịch trình: {schedule_info}")
                    info(f"📦 Lưu trữ tại: {provider_display}")
            elif action == "update":
                success(f"✅ Đã cập nhật lịch trình backup cho website {domain}.")
                
                # Hiển thị thông tin lịch trình đã cập nhật
                if config:
                    schedule_type = config["schedule_type"]
                    hour = config["hour"]
                    minute = config["minute"]
                    
                    schedule_info = ""
                    if schedule_type == "daily":
                        schedule_info = f"hàng ngày lúc {hour:02d}:{minute:02d}"
                    elif schedule_type == "weekly":
                        day = config["day_of_week"]
                        day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                        day_name = day_names[day] if 0 <= day < len(day_names) else f"ngày {day}"
                        schedule_info = f"hàng tuần vào {day_name} lúc {hour:02d}:{minute:02d}"
                    elif schedule_type == "monthly":
                        day = config["day_of_month"]
                        schedule_info = f"hàng tháng vào ngày {day} lúc {hour:02d}:{minute:02d}"
                    
                    # Hiển thị provider
                    provider = config["provider"]
                    provider_display = provider
                    if provider == "local":
                        provider_display = "lưu trữ local"
                    elif provider.startswith("rclone:"):
                        remote_name = provider.split(":")[1]
                        provider_display = f"lưu trữ đám mây ({remote_name})"
                    
                    info(f"⏰ Lịch trình mới: {schedule_info}")
                    info(f"📦 Lưu trữ tại: {provider_display}")
        else:
            error(f"❌ Lỗi xử lý lịch trình backup: {message}")


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_schedule_backup():
    """
    Hàm tiện ích để lên lịch backup tự động.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình lên lịch hoặc None nếu bị hủy
    """
    prompt = ScheduleBackupPrompt()
    return prompt.run()