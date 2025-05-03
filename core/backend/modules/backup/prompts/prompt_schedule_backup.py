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
from core.backend.modules.website.website_utils import select_website, get_site_config, set_site_config
from core.backend.models.config import BackupSchedule, CloudConfig, SiteBackup
from core.backend.modules.cron.models.cron_job import CronJob
from core.backend.modules.cron.cron_manager import CronManager


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
        
        # Kiểm tra lịch trình hiện tại
        site_config = get_site_config(domain)
        has_existing_schedule = (site_config and site_config.backup and
                                site_config.backup.schedule and
                                site_config.backup.schedule.enabled)
        
        # Hành động dựa trên trạng thái hiện tại
        if has_existing_schedule:
            # Hiển thị thông tin lịch trình hiện tại
            current_schedule = site_config.backup.schedule
            info(f"⏱️ Lịch trình hiện tại: {self._format_schedule(current_schedule)}")
            
            # Hỏi người dùng muốn cập nhật hay xóa lịch trình
            action = select(
                "🔍 Bạn muốn làm gì với lịch trình hiện tại?",
                choices=[
                    "Cập nhật lịch trình",
                    "Vô hiệu hóa lịch trình",
                    "Xóa lịch trình",
                    "Quay lại"
                ]
            ).ask()
            
            if not action or action == "Quay lại":
                info("Đã huỷ thao tác.")
                return None
                
            if action == "Xóa lịch trình":
                if confirm("⚠️ Xác nhận xóa lịch trình backup tự động?").ask():
                    return {
                        "domain": domain,
                        "action": "delete"
                    }
                info("Đã huỷ thao tác.")
                return None
                
            if action == "Vô hiệu hóa lịch trình":
                return {
                    "domain": domain,
                    "action": "disable"
                }
                
            # Nếu chọn cập nhật, tiếp tục với thông tin hiện tại
            current_values = {
                "schedule_type": current_schedule.schedule_type,
                "hour": current_schedule.hour,
                "minute": current_schedule.minute,
                "day_of_week": current_schedule.day_of_week,
                "day_of_month": current_schedule.day_of_month,
                "retention_count": current_schedule.retention_count,
                "cloud_sync": current_schedule.cloud_sync
            }
        else:
            # Tạo mới
            action = "create"
            current_values = {
                "schedule_type": "daily",
                "hour": 1,
                "minute": 0,
                "day_of_week": None,
                "day_of_month": None,
                "retention_count": 3,
                "cloud_sync": False
            }
        
        # Thu thập thông tin lịch trình
        schedule_type = select(
            "🔄 Chọn tần suất backup:",
            choices=[
                "Hàng ngày",
                "Hàng tuần",
                "Hàng tháng"
            ],
            default="Hàng ngày" if current_values["schedule_type"] == "daily" else 
                    "Hàng tuần" if current_values["schedule_type"] == "weekly" else
                    "Hàng tháng"
        ).ask()
        
        if not schedule_type:
            info("Đã huỷ thao tác.")
            return None
        
        # Chọn giờ trong ngày
        hour_choices = [f"{h:02d}" for h in range(24)]
        hour = select(
            "🕒 Chọn giờ thực hiện backup (0-23):",
            choices=hour_choices,
            default=f"{current_values['hour']:02d}"
        ).ask()
        
        if not hour:
            info("Đã huỷ thao tác.")
            return None
        
        hour = int(hour)
        
        # Chọn phút
        minute_choices = ["00", "15", "30", "45"]
        minute = select(
            "🕒 Chọn phút (0-59):",
            choices=minute_choices,
            default=f"{current_values['minute']:02d}" if current_values['minute'] in [0, 15, 30, 45] else "00"
        ).ask()
        
        if not minute:
            info("Đã huỷ thao tác.")
            return None
        
        minute = int(minute)
        
        # Thông tin bổ sung dựa trên loại lịch trình
        day_of_week = None
        day_of_month = None
        
        if schedule_type == "Hàng tuần":
            days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
            default_day = days[current_values["day_of_week"]] if current_values["day_of_week"] is not None else "Thứ Hai"
            
            selected_day = select(
                "📅 Chọn ngày trong tuần:",
                choices=days,
                default=default_day
            ).ask()
            
            if not selected_day:
                info("Đã huỷ thao tác.")
                return None
            
            day_of_week = days.index(selected_day)
            
        elif schedule_type == "Hàng tháng":
            day_choices = [str(d) for d in range(1, 32)]
            default_day = str(current_values["day_of_month"]) if current_values["day_of_month"] is not None else "1"
            
            selected_day = select(
                "📅 Chọn ngày trong tháng (1-31):",
                choices=day_choices,
                default=default_day
            ).ask()
            
            if not selected_day:
                info("Đã huỷ thao tác.")
                return None
            
            day_of_month = int(selected_day)
        
        # Chọn số lượng bản backup giữ lại
        retention_choices = ["1", "3", "5", "10", "Tất cả"]
        default_retention = "Tất cả" if current_values["retention_count"] == 0 else str(current_values["retention_count"])
        
        retention = select(
            "🔢 Số lượng bản backup gần nhất muốn giữ lại:",
            choices=retention_choices,
            default=default_retention
        ).ask()
        
        if not retention:
            info("Đã huỷ thao tác.")
            return None
        
        retention_count = 0 if retention == "Tất cả" else int(retention)
        
        # Cấu hình đồng bộ lên cloud
        cloud_sync = confirm(
            "☁️ Bạn có muốn đồng bộ backup lên cloud storage không?",
            default=current_values["cloud_sync"]
        ).ask()
        
        # Nếu bật đồng bộ cloud, thu thập thông tin
        cloud_config = None
        if cloud_sync:
            # Lấy cấu hình cloud hiện tại nếu có
            current_cloud = None
            if site_config and site_config.backup and site_config.backup.cloud_config:
                current_cloud = site_config.backup.cloud_config
            
            # Nhập tên remote rclone
            remote_name = text(
                "Nhập tên remote rclone:",
                default=current_cloud.remote_name if current_cloud else ""
            ).ask()
            
            if not remote_name:
                info("Đã huỷ thao tác.")
                return None
            
            # Nhập đường dẫn trong remote
            remote_path = text(
                "Nhập đường dẫn trong remote:",
                default=current_cloud.remote_path if current_cloud else f"backup/{domain}"
            ).ask()
            
            if not remote_path:
                info("Đã huỷ thao tác.")
                return None
            
            cloud_config = {
                "provider": "rclone",
                "remote_name": remote_name,
                "remote_path": remote_path,
                "enabled": True
            }
        
        # Chuyển đổi loại lịch trình
        schedule_type_map = {
            "Hàng ngày": "daily",
            "Hàng tuần": "weekly",
            "Hàng tháng": "monthly"
        }
        
        # Xác nhận cấu hình
        if not confirm("⚠️ Xác nhận áp dụng lịch trình backup tự động?").ask():
            info("Đã huỷ thao tác.")
            return None
        
        # Trả về thông tin đã thu thập
        return {
            "domain": domain,
            "action": action,
            "schedule": {
                "schedule_type": schedule_type_map[schedule_type],
                "hour": hour,
                "minute": minute,
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "retention_count": retention_count,
                "cloud_sync": cloud_sync
            },
            "cloud_config": cloud_config
        }
    
    def _process(self, inputs):
        """
        Thực hiện việc tạo, cập nhật hoặc xóa lịch trình backup.
        
        Args:
            inputs: Dict chứa thông tin về lịch trình backup
            
        Returns:
            dict: Kết quả xử lý
        """
        domain = inputs["domain"]
        action = inputs["action"]
        
        # Lấy cấu hình website
        site_config = get_site_config(domain)
        if not site_config:
            error(f"❌ Không tìm thấy cấu hình cho website {domain}.")
            return None
        
        # Đảm bảo có phần backup trong cấu hình
        if not site_config.backup:
            site_config.backup = SiteBackup()
        
        # Khởi tạo CronManager
        cron_manager = CronManager()
        
        # Xử lý theo hành động
        if action == "delete":
            # Xóa công việc cron nếu có
            if site_config.backup.job_id:
                cron_manager.remove_job(site_config.backup.job_id)
            
            # Xóa cấu hình lịch trình
            site_config.backup.schedule = None
            site_config.backup.job_id = None
            
            # Lưu cấu hình mới
            set_site_config(domain, site_config)
            
            return {
                "domain": domain,
                "action": "delete",
                "success": True
            }
        
        elif action == "disable":
            # Vô hiệu hóa công việc cron
            if site_config.backup.job_id:
                # Use the disable_job method which now handles versions safely
                cron_manager.disable_job(site_config.backup.job_id)
            
            # Cập nhật cấu hình
            if site_config.backup.schedule:
                site_config.backup.schedule.enabled = False
                set_site_config(domain, site_config)
            
            return {
                "domain": domain,
                "action": "disable",
                "success": True
            }
        
        else:  # create or update
            # Tạo đối tượng BackupSchedule
            schedule_data = inputs["schedule"]
            schedule = BackupSchedule(
                enabled=True,
                schedule_type=schedule_data["schedule_type"],
                hour=schedule_data["hour"],
                minute=schedule_data["minute"],
                day_of_week=schedule_data["day_of_week"],
                day_of_month=schedule_data["day_of_month"],
                retention_count=schedule_data["retention_count"],
                cloud_sync=schedule_data["cloud_sync"]
            )
            
            # Cập nhật hoặc tạo cấu hình cloud nếu cần
            cloud_config = inputs.get("cloud_config")
            if cloud_config:
                site_config.backup.cloud_config = CloudConfig(
                    provider=cloud_config["provider"],
                    remote_name=cloud_config["remote_name"],
                    remote_path=cloud_config["remote_path"],
                    enabled=cloud_config["enabled"]
                )
            elif schedule.cloud_sync and not site_config.backup.cloud_config:
                # Tạo cấu hình cloud mặc định nếu chưa có
                site_config.backup.cloud_config = CloudConfig(
                    remote_path=f"backup/{domain}"
                )
            
            # Cập nhật lịch trình
            site_config.backup.schedule = schedule
            
            # Tạo biểu thức cron
            cron_expr = self._create_cron_expression(schedule)
            
            # Tham số cho công việc
            job_params = {
                "retention_count": schedule.retention_count,
                "cloud_sync": schedule.cloud_sync
            }
            
            if site_config.backup.cloud_config and schedule.cloud_sync:
                job_params["cloud_config"] = asdict(site_config.backup.cloud_config)
            
            # Tạo hoặc cập nhật công việc cron
            if site_config.backup.job_id:
                # Cập nhật công việc hiện có
                job = cron_manager.get_job(site_config.backup.job_id)
                if job:
                    # Cập nhật thông tin
                    job.schedule = cron_expr
                    job.parameters = job_params
                    job.enabled = True
                    cron_manager.update_job(job)
                else:
                    # Công việc không tồn tại, tạo mới
                    job = CronJob(
                        id=f"backup_{domain}_{int(time.time())}",
                        job_type="backup",
                        schedule=cron_expr,
                        target_id=domain,
                        parameters=job_params,
                        enabled=True,
                        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    cron_manager.add_job(job)
                    site_config.backup.job_id = job.id
            else:
                # Tạo công việc mới
                job = CronJob(
                    id=f"backup_{domain}_{int(time.time())}",
                    job_type="backup",
                    schedule=cron_expr,
                    target_id=domain,
                    parameters=job_params,
                    enabled=True,
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                cron_manager.add_job(job)
                site_config.backup.job_id = job.id
            
            # Lưu cấu hình mới
            set_site_config(domain, site_config)
            
            return {
                "domain": domain,
                "action": "create_or_update",
                "success": True,
                "schedule": schedule,
                "job_id": site_config.backup.job_id,
                "cron_expression": cron_expr
            }
    
    def _show_results(self):
        """
        Hiển thị kết quả lên lịch backup.
        
        Sử dụng self.result để hiển thị kết quả.
        """
        if not self.result:
            return
        
        domain = self.result["domain"]
        action = self.result["action"]
        success = self.result.get("success", False)
        
        if not success:
            error(f"❌ Không thể cấu hình lịch trình backup cho {domain}.")
            return
        
        if action == "delete":
            success(f"✅ Đã xóa lịch trình backup tự động cho website {domain}.")
            
        elif action == "disable":
            success(f"✅ Đã vô hiệu hóa lịch trình backup tự động cho website {domain}.")
            
        elif action == "create_or_update":
            schedule = self.result["schedule"]
            job_id = self.result["job_id"]
            cron_expr = self.result["cron_expression"]
            
            success(f"✅ Đã cấu hình lịch trình backup tự động cho website {domain}.")
            info(f"⏱️ Lịch trình: {self._format_schedule(schedule)}")
            info(f"🔄 Biểu thức Cron: {cron_expr}")
            info(f"🔑 Job ID: {job_id}")
            
            if schedule.cloud_sync:
                info("☁️ Đồng bộ lên cloud storage: Bật")
            else:
                info("☁️ Đồng bộ lên cloud storage: Tắt")
            
            retention = "Tất cả" if schedule.retention_count == 0 else str(schedule.retention_count)
            info(f"🔢 Số lượng backup giữ lại: {retention}")
    
    def _format_schedule(self, schedule):
        """
        Định dạng lịch trình để hiển thị.
        
        Args:
            schedule: Đối tượng BackupSchedule
            
        Returns:
            str: Chuỗi mô tả lịch trình
        """
        if not schedule:
            return "Không có"
        
        hour_min = f"{schedule.hour:02d}:{schedule.minute:02d}"
        
        if schedule.schedule_type == "daily":
            result = f"Hàng ngày lúc {hour_min}"
        elif schedule.schedule_type == "weekly" and schedule.day_of_week is not None:
            days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
            day_name = days[schedule.day_of_week]
            result = f"{day_name} hàng tuần lúc {hour_min}"
        elif schedule.schedule_type == "monthly" and schedule.day_of_month is not None:
            result = f"Ngày {schedule.day_of_month} hàng tháng lúc {hour_min}"
        else:
            result = f"Lịch trình không hợp lệ"
        
        if not schedule.enabled:
            result += " (đã vô hiệu hóa)"
        
        return result
    
    def _create_cron_expression(self, schedule):
        """
        Tạo biểu thức cron từ cấu hình lịch trình.
        
        Args:
            schedule: Đối tượng BackupSchedule
            
        Returns:
            str: Biểu thức cron (VD: "0 2 * * *")
        """
        minute = schedule.minute
        hour = schedule.hour
        day_of_month = "*"
        month = "*"
        day_of_week = "*"
        
        if schedule.schedule_type == "weekly" and schedule.day_of_week is not None:
            day_of_week = str(schedule.day_of_week)
        
        if schedule.schedule_type == "monthly" and schedule.day_of_month is not None:
            day_of_month = str(schedule.day_of_month)
        
        return f"{minute} {hour} {day_of_month} {month} {day_of_week}"


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_schedule_backup():
    """
    Hàm tiện ích để lên lịch backup tự động.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình lên lịch backup hoặc None nếu bị hủy
    """
    prompt = ScheduleBackupPrompt()
    return prompt.run()