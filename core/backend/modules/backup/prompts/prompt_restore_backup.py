"""
Module xử lý khôi phục backup website.
"""
from questionary import select, confirm, checkbox
import os
from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.abc.prompt_base import PromptBase
from core.backend.modules.website.website_utils import select_website
from core.backend.modules.backup.backup_restore import (
    get_backup_folders,
    get_backup_info,
    restore_database,
    restore_source_code,
    restart_website
)

class BackupRestorePrompt(PromptBase):
    """
    Lớp xử lý prompt khôi phục backup website.
    
    Triển khai lớp trừu tượng PromptBase với các phương thức:
    - _collect_inputs: Thu thập thông tin domain, backup, và các thành phần cần khôi phục
    - _process: Tiến hành quá trình khôi phục backup
    - _show_results: Hiển thị kết quả khôi phục
    """
    
    def _collect_inputs(self):
        """
        Thu thập đầu vào từ người dùng về website, backup, và các thành phần cần khôi phục.
        
        Returns:
            dict: Chứa thông tin domain, backup, và thành phần cần khôi phục hoặc None nếu bị hủy
        """
        # Chọn một website sử dụng hàm select_website có sẵn
        domain = select_website("🌐 Chọn website để khôi phục backup:")
        
        if not domain:
            # Thông báo lỗi đã được hiển thị trong hàm select_website
            return None
        
        # Lấy thông tin về các thư mục backup
        backup_dir, backup_folders, last_backup_info = get_backup_folders(domain)
        
        if not backup_folders:
            return None  # Thông báo lỗi đã được hiển thị trong hàm get_backup_folders
        
        # Tạo danh sách hiển thị với thông tin thêm về thời gian và kích thước
        display_choices = []
        backup_info_list = []
        
        for folder in backup_folders:
            backup_info = get_backup_info(backup_dir, folder, last_backup_info)
            backup_info_list.append(backup_info)
            
            if "error" in backup_info:
                display_choices.append(f"{folder} (Không thể lấy thông tin: {backup_info['error']})")
            else:
                status = "✅ Là bản backup gần nhất" if backup_info["is_latest"] else ""
                display_choices.append(f"{folder} [{backup_info['time']}] [{backup_info['size']}] {status}")
        
        # Chọn một backup để khôi phục
        selected_backup = select(
            "📁 Chọn bản backup để khôi phục:",
            choices=display_choices
        ).ask()
        
        if not selected_backup:
            info("Đã huỷ thao tác khôi phục backup.")
            return None
        
        # Lấy thông tin backup đã chọn
        folder_name = selected_backup.split(" ")[0]
        selected_index = next((i for i, item in enumerate(backup_info_list) if item["folder"] == folder_name), -1)
        
        if selected_index == -1:
            error(f"❌ Không tìm thấy thông tin cho bản backup đã chọn.")
            return None
            
        backup_info = backup_info_list[selected_index]
        info(f"📂 Bạn đã chọn bản backup: {folder_name}")
        
        # Kiểm tra xem có file cần thiết không
        if not backup_info.get("archive_file") and not backup_info.get("sql_file"):
            error(f"❌ Không tìm thấy file backup (tar.gz hoặc sql) trong thư mục {folder_name}.")
            return None
        
        # Cho người dùng chọn các thành phần để khôi phục
        components = []
        
        if backup_info.get("archive_file"):
            components.append("Mã nguồn website")
        
        if backup_info.get("sql_file"):
            components.append("Database")
        
        if not components:
            error("❌ Không có thành phần nào để khôi phục.")
            return None
        
        selected_components = checkbox(
            "🔄 Chọn các thành phần để khôi phục (dùng phím space để chọn):",
            choices=components
        ).ask()
        
        if not selected_components:
            info("Đã huỷ thao tác khôi phục backup.")
            return None
        
        # Xác nhận khôi phục
        if not confirm(f"⚠️ CẢNH BÁO: Khôi phục sẽ ghi đè lên dữ liệu hiện tại của website {domain}. Bạn có chắc chắn muốn tiếp tục?").ask():
            info("Đã huỷ thao tác khôi phục backup.")
            return None
        
        # Hỏi người dùng có muốn xóa database hiện tại không nếu cần khôi phục database
        reset_db = False
        if "Database" in selected_components and backup_info.get("sql_file"):
            reset_db = confirm("🗑️ Bạn có muốn xóa dữ liệu database hiện tại trước khi khôi phục?").ask()
        
        # Hỏi người dùng có muốn khởi động lại website không
        restart = confirm(f"🔄 Bạn có muốn khởi động lại website {domain} sau khi khôi phục xong không?").ask()
        
        # Trả về thông tin đã thu thập
        return {
            "domain": domain,
            "backup_info": backup_info,
            "selected_components": selected_components,
            "reset_db": reset_db,
            "restart": restart
        }
    
    def _process(self, inputs):
        """
        Xử lý việc khôi phục backup dựa trên thông tin đầu vào.
        
        Args:
            inputs: Dict chứa thông tin domain, backup, và thành phần cần khôi phục
            
        Returns:
            dict: Kết quả xử lý bao gồm trạng thái thành công và chi tiết khôi phục
        """
        domain = inputs["domain"]
        backup_info = inputs["backup_info"]
        selected_components = inputs["selected_components"]
        reset_db = inputs["reset_db"]
        restart = inputs["restart"]
        
        # Tiến hành khôi phục
        info(f"🔄 Bắt đầu quá trình khôi phục backup cho website {domain}...")
        restore_success = True
        component_results = {}
        
        # Khôi phục database
        if "Database" in selected_components and backup_info.get("sql_file"):
            sql_file = backup_info["sql_file"]
            info(f"💾 Khôi phục database từ file: {os.path.basename(sql_file)}")
            
            db_success = restore_database(domain, sql_file, reset_db)
            restore_success = restore_success and db_success
            component_results["database"] = {
                "success": db_success,
                "file": os.path.basename(sql_file),
                "reset": reset_db
            }
        
        # Khôi phục mã nguồn
        if "Mã nguồn website" in selected_components and backup_info.get("archive_file"):
            archive_file = backup_info["archive_file"]
            info(f"📦 Khôi phục mã nguồn từ file: {os.path.basename(archive_file)}")
            
            # Hỏi người dùng xác nhận
            if confirm(f"⚠️ Quá trình này sẽ GHI ĐÈ lên tất cả file trong thư mục wordpress của {domain}. Tiếp tục?").ask():
                source_success = restore_source_code(domain, archive_file)
                restore_success = restore_success and source_success
                component_results["source_code"] = {
                    "success": source_success,
                    "file": os.path.basename(archive_file)
                }
            else:
                info("Đã huỷ thao tác khôi phục mã nguồn.")
                component_results["source_code"] = {
                    "success": False,
                    "cancelled": True
                }
        
        # Khởi động lại website nếu được yêu cầu
        restart_result = None
        if restore_success and restart:
            restart_result = restart_website(domain)
            component_results["restart"] = {
                "success": restart_result
            }
        
        # Trả về kết quả
        return {
            "domain": domain,
            "restore_success": restore_success,
            "component_results": component_results,
            "backup_info": backup_info
        }
    
    def _show_results(self):
        """
        Hiển thị kết quả khôi phục backup.
        
        Sử dụng self.result để hiển thị kết quả xử lý.
        """
        if not self.result:
            return
        
        domain = self.result["domain"]
        restore_success = self.result["restore_success"]
        component_results = self.result["component_results"]
        
        # Tổng hợp kết quả và hiển thị
        if restore_success:
            success(f"🎉 Đã hoàn tất khôi phục backup cho website {domain}.")
            
            # Hiển thị chi tiết từng thành phần
            for component, result in component_results.items():
                if component == "database" and result["success"]:
                    info(f"  ✅ Database: Đã khôi phục từ {result['file']}" + 
                         f" (Đã xóa dữ liệu cũ: {'Có' if result['reset'] else 'Không'})")
                elif component == "source_code":
                    if result.get("cancelled"):
                        info(f"  ⏩ Mã nguồn: Đã bỏ qua theo yêu cầu")
                    elif result["success"]:
                        info(f"  ✅ Mã nguồn: Đã khôi phục từ {result['file']}")
                elif component == "restart":
                    if result["success"]:
                        info(f"  ✅ Website đã được khởi động lại thành công")
                    else:
                        warn(f"  ⚠️ Không thể khởi động lại website tự động. Hãy khởi động lại thủ công nếu cần.")
        else:
            error(f"❌ Quá trình khôi phục backup gặp một số lỗi. Vui lòng kiểm tra lại website {domain}.")
            
            # Hiển thị chi tiết lỗi từng thành phần
            for component, result in component_results.items():
                if component == "database":
                    status = "✅ Thành công" if result["success"] else "❌ Thất bại"
                    info(f"  • Database: {status}")
                elif component == "source_code":
                    if result.get("cancelled"):
                        info(f"  • Mã nguồn: ⏩ Đã bỏ qua theo yêu cầu")
                    else:
                        status = "✅ Thành công" if result["success"] else "❌ Thất bại"
                        info(f"  • Mã nguồn: {status}")


# Hàm tiện ích để tương thích với giao diện cũ
@log_call
def prompt_restore_backup():
    """
    Hàm tiện ích để chạy prompt khôi phục backup.
    Duy trì tương thích với giao diện cũ.
    
    Returns:
        Kết quả từ quá trình khôi phục hoặc None nếu bị hủy
    """
    prompt = BackupRestorePrompt()
    return prompt.run()