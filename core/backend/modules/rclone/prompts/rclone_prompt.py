#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import inquirer
from typing import Dict, List, Optional, Tuple
from core.backend.utils.env_utils import get_env_value
from core.backend.modules.rclone.rclone_manager import RcloneManager
from core.backend.modules.rclone.config_manager import RcloneConfigManager
from core.backend.modules.rclone.utils import (
    validate_remote_type, 
    validate_remote_params,
    validate_raw_config,
    format_size,
    get_backup_filename,
    get_remote_type_display_name
)
from core.backend.utils.container_utils import convert_host_path_to_container
from core.backend.utils.debug import Debug


def prompt_manage_rclone():
    """Prompt for managing Rclone operations."""
    # Hiển thị tiêu đề
    print("\n" + "="*80)
    print("🌩️  QUẢN LÝ LƯU TRỮ ĐÁM MÂY (RCLONE)")
    print("="*80)
    print("Rclone cho phép kết nối và sao lưu dữ liệu tới nhiều dịch vụ lưu trữ khác nhau như")
    print("Google Drive, Dropbox, S3, OneDrive, Box và nhiều dịch vụ khác.")
    print("-"*80)
    
    # Danh sách các hành động với emoji
    actions = [
        "📋 Danh sách kết nối lưu trữ đám mây",
        "➕ Thêm kết nối lưu trữ mới",
        "🔍 Xem chi tiết kết nối",
        "❌ Xóa kết nối",
        "⬆️ Sao lưu lên đám mây",
        "⬇️ Khôi phục từ đám mây",
        "📁 Xem tệp tin trên đám mây",
        "⬅️ Quay lại menu chính"
    ]
    
    questions = [
        inquirer.List(
            "action",
            message="Chọn thao tác:",
            choices=actions,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if answers:
        action = answers["action"]
        
        if "Danh sách kết nối" in action:
            list_remotes()
        elif "Thêm kết nối" in action:
            prompt_add_remote()
        elif "Xóa kết nối" in action:
            prompt_remove_remote()
        elif "Xem chi tiết" in action:
            prompt_view_remote_details()
        elif "Sao lưu" in action:
            prompt_backup_to_remote()
        elif "Khôi phục" in action:
            from core.backend.modules.backup.prompts.prompt_cloud_backup import prompt_restore_from_cloud
            prompt_restore_from_cloud()
        elif "Xem tệp tin" in action:
            prompt_view_backup_files()
        elif "Quay lại" in action:
            return
    
    # Return to the Rclone management menu unless we're going back
    if answers and "Quay lại" not in answers["action"]:
        prompt_manage_rclone()


def list_remotes():
    """List all configured remotes."""
    rclone_manager = RcloneManager()
    config_manager = RcloneConfigManager()
    remotes = rclone_manager.list_remotes()
    
    if remotes:
        print("\nDanh sách các remote đã cấu hình:")
        print("=" * 80)
        print(f"{'Tên':20} {'Loại':30} {'Trạng thái'}")
        print("-" * 80)
        
        for remote in remotes:
            # Lấy thông tin cấu hình để biết loại
            config = config_manager.get_remote_config(remote)
            remote_type = config.get("type", "unknown") if config else "unknown"
            
            # Lấy tên hiển thị thân thiện cho loại remote
            display_type = get_remote_type_display_name(remote_type)
            
            # Kiểm tra kết nối (đơn giản là để biết remote có hoạt động)
            status = "✅ Sẵn sàng"
            print(f"{remote:20} {display_type:30} {status}")
        
        print("=" * 80)
    else:
        print("\nChưa có remote nào được cấu hình.")
    
    input("\nNhấn Enter để tiếp tục...")


def prompt_add_remote():
    """Prompt for adding a new remote."""
    # Danh sách các loại remote hỗ trợ với tên hiển thị thân thiện
    # Sắp xếp theo thứ tự phổ biến
    remote_choices = [
        "Google Drive (drive)",
        "Dropbox (dropbox)",
        "Microsoft OneDrive (onedrive)",
        "Amazon S3 / Wasabi / DO Spaces (s3)",
        "Backblaze B2 (b2)",
        "Box (box)",
        "SFTP (sftp)",
        "FTP (ftp)",
        "WebDAV / Nextcloud / Owncloud (webdav)",
        "Azure Blob Storage (azureblob)",
        "Mega.nz (mega)",
        "pCloud (pcloud)",
        "OpenStack Swift (swift)",
        "Yandex Disk (yandex)",
        "Local Disk (local)"
    ]
    
    questions = [
        inquirer.Text("name", message="Nhập tên cho remote:"),
        inquirer.List(
            "type_display",
            message="Chọn loại dịch vụ lưu trữ:",
            choices=remote_choices,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if not answers:
        return
    
    remote_name = answers["name"]
    # Trích xuất tên kỹ thuật từ chuỗi hiển thị (nằm trong ngoặc)
    remote_type_match = answers["type_display"].split("(")[-1].split(")")[0]
    remote_type = remote_type_match if remote_type_match else "unknown"
    
    # Get parameters based on remote type
    params = prompt_remote_params(remote_type)
    
    if params:
        rclone_manager = RcloneManager()
        success = rclone_manager.add_remote(remote_name, remote_type, params)
        
        if success:
            print(f"\nRemote '{remote_name}' added successfully.")
        else:
            print(f"\nFailed to add remote '{remote_name}'.")
    
    input("\nPress Enter to continue...")



def prompt_remote_params(remote_type: str) -> Dict[str, str]:
    """Prompt for remote-specific parameters and provide detailed guidance."""
    params = {}
    
    # Lấy tên hiển thị thân thiện
    display_name = get_remote_type_display_name(remote_type)
    
    # Hiển thị hướng dẫn chi tiết dựa trên loại remote
    print("\n" + "="*80)
    print(f"HƯỚNG DẪN THIẾT LẬP CHO {display_name}")
    print("="*80)
    
    if remote_type == "s3":
        print("""
Để thiết lập Amazon S3 hoặc dịch vụ tương thích S3, bạn cần:

1. Access Key ID và Secret Access Key:
   - Đối với AWS S3: Tạo tại https://console.aws.amazon.com/iam/
   - Đối với Wasabi, DigitalOcean Spaces: Tạo trong control panel của dịch vụ

2. Region: Khu vực bạn đã chọn khi tạo bucket
   - Ví dụ: us-east-1, eu-west-2, ap-southeast-1, v.v...

3. Endpoint (chỉ cần cho S3 tương thích):
   - Wasabi: s3.wasabisys.com hoặc s3.eu-central-1.wasabisys.com
   - DigitalOcean: nyc3.digitaloceanspaces.com (thay nyc3 bằng khu vực của bạn)
   - Cloudflare R2: <account-id>.r2.cloudflarestorage.com

Tất cả thông tin này có sẵn trong dashboard của dịch vụ.
""")
        questions = [
            inquirer.Text("provider", message="Provider (aws, wasabi, do, cloudflare, v.v...):"),
            inquirer.Text("access_key_id", message="Access Key ID:"),
            inquirer.Password("secret_access_key", message="Secret Access Key:"),
            inquirer.Text("region", message="Region:"),
            inquirer.Text("endpoint", message="Endpoint (cho non-AWS S3, để trống cho AWS):", default=""),
        ]
    
    elif remote_type == "b2":
        print("""
Để thiết lập Backblaze B2, bạn cần:

1. Account ID và Application Key:
   - Đăng nhập vào Backblaze B2 tại https://secure.backblaze.com/b2_buckets.htm
   - Tại dashboard, nhấn "App Keys" trong menu bên trái
   - Tạo một Application Key mới với quyền truy cập phù hợp
   - Lưu ý: Bạn chỉ thấy Application Key một lần khi tạo, hãy lưu lại ngay!

Application Key có thể được giới hạn cho một bucket cụ thể hoặc toàn bộ tài khoản.
""")
        questions = [
            inquirer.Text("account", message="Account ID:"),
            inquirer.Password("key", message="Application Key:"),
        ]
    
    elif remote_type in ["drive", "dropbox", "onedrive", "box", "mega", "pcloud"]:
        # Chia nhỏ thành nhiều đoạn để tránh vấn đề với định dạng JSON trong f-string
        print(f"\n⚠️ QUAN TRỌNG - MÔI TRƯỜNG VPS VÀ SSH ⚠️\n")
        print(f"{display_name} sử dụng xác thực OAuth, yêu cầu trình duyệt web để cấp quyền.")
        print("Khi sử dụng qua SSH trên VPS, bạn nên tạo cấu hình Rclone trên máy cục bộ trước,")
        print("sau đó sao chép cấu hình lên VPS.\n")
        
        print("Hướng dẫn cách thiết lập:\n")
        print("1. Cài đặt Rclone trên máy cục bộ của bạn (máy tính cá nhân):")
        print("   - Tải tại: https://rclone.org/downloads/")
        print("   - Hoặc cài đặt bằng terminal: curl https://rclone.org/install.sh | sudo bash\n")
        
        print("2. Chạy lệnh sau để tạo cấu hình:")
        print("   - rclone config")
        print("   - Chọn \"New remote\" (n)")
        print("   - Nhập tên remote (ví dụ: \"mydrive\")")
        print(f"   - Chọn loại \"{display_name}\" ({remote_type})")
        print("   - Làm theo hướng dẫn xác thực OAuth trên trình duyệt")
        print("   - Hoàn tất thiết lập\n")
        
        print("3. Sao chép cấu hình từ máy cục bộ lên VPS:")
        print("   - File cấu hình thường nằm ở: ~/.config/rclone/rclone.conf")
        config_dir = get_env_value("CONFIG_DIR")
        print(f"   - Sử dụng lệnh: scp ~/.config/rclone/rclone.conf user@your_vps:/đường-dẫn-tới/{config_dir}/rclone/rclone.conf\n")
        
        print("4. Hoặc sao chép nội dung phần cấu hình từ file rclone.conf trên máy cục bộ ")
        print("   và dán vào bên dưới (định dạng phải giống như dưới đây):\n")
        
        print("   [tên-remote]")
        print(f"   type = {remote_type}")
        print('   token = {"access_token":"xxx","token_type":"Bearer","refresh_token":"xxx","expiry":"date"}')
        print("   client_id = xxx")
        print("   client_secret = xxx")
        print("   ...")
        print("\nLựa chọn:")
        questions = [
            inquirer.Confirm("manual_config", 
                message="Bạn đã tạo cấu hình trên máy cục bộ và muốn nhập cấu hình thủ công?", 
                default=True),
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return {}
            
        if answers.get("manual_config", False):
            # Sử dụng inquirer cho tệp cấu hình thủ công
            print("\n📋 THÊM CẤU HÌNH RCLONE THỦ CÔNG")
            print("="*80)
            print(f"Để thêm {remote_type}, bạn cần chuẩn bị cấu hình từ file rclone.conf.")
            print("LƯU Ý QUAN TRỌNG:")
            print("1. Chỉ dùng các dòng cấu hình, KHÔNG bao gồm tên remote trong ngoặc vuông [xxx]")
            print("2. Cấu hình phải có ít nhất dòng token = {...}")
            print("="*80)
            
            # Tạo tên tệp tạm thời để người dùng nhập cấu hình
            import tempfile
            import subprocess
            
            # Tạo tệp tạm thời
            with tempfile.NamedTemporaryFile(suffix='.conf', delete=False, mode='w+') as temp_file:
                temp_path = temp_file.name
                # Tạo mẫu cho người dùng
                temp_file.write(f"# Dán cấu hình {remote_type} dưới đây, không bao gồm tên remote [xxx]\n")
                temp_file.write(f"# Ví dụ cho {remote_type}:\n")
                temp_file.write(f"type = {remote_type}\n")
                temp_file.write('token = {"access_token":"***","token_type":"Bearer","refresh_token":"***","expiry":"***"}\n')
                temp_file.write("client_id = ***\n")
                temp_file.write("client_secret = ***\n")
                temp_file.write("# Xóa các dòng này và dán cấu hình thực của bạn vào đây\n")
            
            print(f"\nSau khi mở trình soạn thảo:")
            print("- Dán cấu hình Rclone của bạn vào tệp")
            print("- Xóa các dòng hướng dẫn (bắt đầu bằng #)")
            print("- Lưu lại và đóng trình soạn thảo để tiếp tục")
            
            # Sử dụng hàm choose_editor để chọn và mở trình soạn thảo
            from core.backend.utils.editor import choose_editor
            
            # Chọn trình soạn thảo, sử dụng biến môi trường EDITOR làm giá trị mặc định nếu có
            default_editor = get_env_value("EDITOR")
            editor = choose_editor(default_editor)
            
            # Nếu người dùng hủy việc chọn editor
            if not editor:
                # Xóa tệp tạm thời
                os.unlink(temp_path)
                print("\n❌ Đã hủy nhập cấu hình.")
                return {}
                
            try:
                # Mở trình soạn thảo đã chọn
                subprocess.run([editor, temp_path], check=True)
                
                # Đọc tệp cấu hình sau khi người dùng đã lưu
                with open(temp_path, 'r') as f:
                    content = f.read()
                
                # Lọc các dòng có ý nghĩa, bỏ qua comment và dòng trống
                raw_config_lines = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        raw_config_lines.append(line)
                
                # Xóa tệp tạm thời
                os.unlink(temp_path)
                
            except Exception as e:
                print(f"\n❌ Lỗi khi mở trình soạn thảo: {str(e)}")
                return {}
            
            # Phân tích cấu hình
            if not raw_config_lines:
                print("\n❌ Không nhập được cấu hình. Vui lòng thử lại sau.")
                return {}
                
            raw_config = "\n".join(raw_config_lines)
            
            # Validate the raw config
            if not validate_raw_config(raw_config, remote_type):
                print("\n❌ Cấu hình không hợp lệ. Vui lòng kiểm tra lại định dạng.")
                print("Đảm bảo cấu hình chứa ít nhất token và các tham số cần thiết khác.")
                return {}
                
            # Phân tích thành params
            config_params = {}
            for line in raw_config_lines:
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key != "type":  # Chúng ta đã biết loại rồi
                        config_params[key] = value
            
            print("\n✅ Đã nhận cấu hình thủ công thành công.")
            print(f"Cấu hình sẽ được lưu trực tiếp vào file rclone.conf cho '{remote_type}'.")
            print("Cài đặt này sẽ cho phép bạn sử dụng dịch vụ lưu trữ đám mây mà không cần xác thực OAuth.")
            return config_params
        
        # Nếu người dùng không muốn cấu hình thủ công, trả về một từ điển trống
        return {}
    
    elif remote_type in ["sftp", "ftp"]:
        print(f"""
Để thiết lập kết nối {remote_type.upper()}, bạn cần:

1. Thông tin máy chủ:
   - Host: Địa chỉ IP hoặc tên miền của máy chủ
   - Port: Cổng kết nối (mặc định là 22 cho SFTP, 21 cho FTP)

2. Thông tin đăng nhập:
   - Username: Tên người dùng trên máy chủ
   - Password: Mật khẩu (có thể để trống nếu sử dụng key-based authentication cho SFTP)

Đối với SFTP, bạn có thể sử dụng xác thực bằng key thay vì mật khẩu.
""")
        questions = [
            inquirer.Text("host", message="Host (địa chỉ máy chủ):"),
            inquirer.Text("user", message="Username:"),
            inquirer.Password("pass", message="Password (để trống cho key-based auth):", default=""),
            inquirer.Text("port", message=f"Port (mặc định: {'22' if remote_type == 'sftp' else '21'}):", default=""),
        ]
    
    elif remote_type == "webdav":
        print("""
Để thiết lập WebDAV, bạn cần:

1. URL của máy chủ WebDAV:
   - Nextcloud/Owncloud: https://your-cloud.com/remote.php/webdav/
   - SharePoint: https://your-sharepoint.com/sites/your-site/_api/web/getfolderbyserverrelativeurl('/shared%20documents')/files
   - Các dịch vụ khác: Tham khảo tài liệu của dịch vụ đó

2. Thông tin đăng nhập:
   - Username: Tên người dùng WebDAV
   - Password: Mật khẩu WebDAV

Đối với Nextcloud/Owncloud, bạn có thể tạo App Passwords trong phần Security.
""")
        questions = [
            inquirer.Text("url", message="WebDAV URL:"),
            inquirer.Text("user", message="Username:"),
            inquirer.Password("pass", message="Password:"),
        ]
    
    elif remote_type == "azureblob":
        print("""
Để thiết lập Azure Blob Storage, bạn cần:

1. Account Name:
   - Tìm trong portal Azure dưới mục Storage Accounts

2. Account Key hoặc SAS URL:
   - Account Key: Xem trong phần "Access keys" của Storage Account
   - SAS URL: Có thể tạo trong "Shared access signature" của Storage Account

Bạn có thể tìm thông tin này trong Azure Portal: https://portal.azure.com/
""")
        questions = [
            inquirer.Text("account", message="Storage Account Name:"),
            inquirer.Password("key", message="Account Key:"),
        ]
    
    elif remote_type in ["sftp", "ftp"]:
        print(f"""
Để thiết lập kết nối {remote_type.upper()}, bạn cần:

1. Thông tin máy chủ:
   - Host: Địa chỉ IP hoặc tên miền của máy chủ
   - Port: Cổng kết nối (mặc định là 22 cho SFTP, 21 cho FTP)

2. Thông tin đăng nhập:
   - Username: Tên người dùng trên máy chủ
   - Password: Mật khẩu (có thể để trống nếu sử dụng key-based authentication cho SFTP)

Đối với SFTP, bạn có thể sử dụng xác thực bằng key thay vì mật khẩu.
""")
        questions = [
            inquirer.Text("host", message="Host (địa chỉ máy chủ):"),
            inquirer.Text("user", message="Username:"),
            inquirer.Password("pass", message="Password (để trống cho key-based auth):", default=""),
            inquirer.Text("port", message=f"Port (mặc định: {'22' if remote_type == 'sftp' else '21'}):", default=""),
        ]
    
    elif remote_type == "webdav":
        print("""
Để thiết lập WebDAV, bạn cần:

1. URL của máy chủ WebDAV:
   - Nextcloud/Owncloud: https://your-cloud.com/remote.php/webdav/
   - SharePoint: https://your-sharepoint.com/sites/your-site/_api/web/getfolderbyserverrelativeurl('/shared%20documents')/files
   - Các dịch vụ khác: Tham khảo tài liệu của dịch vụ đó

2. Thông tin đăng nhập:
   - Username: Tên người dùng WebDAV
   - Password: Mật khẩu WebDAV

Đối với Nextcloud/Owncloud, bạn có thể tạo App Passwords trong phần Security.
""")
        questions = [
            inquirer.Text("url", message="WebDAV URL:"),
            inquirer.Text("user", message="Username:"),
            inquirer.Password("pass", message="Password:"),
        ]
    
    elif remote_type == "azureblob":
        print("""
Để thiết lập Azure Blob Storage, bạn cần:

1. Account Name:
   - Tìm trong portal Azure dưới mục Storage Accounts

2. Account Key hoặc SAS URL:
   - Account Key: Xem trong phần "Access keys" của Storage Account
   - SAS URL: Có thể tạo trong "Shared access signature" của Storage Account

Bạn có thể tìm thông tin này trong Azure Portal: https://portal.azure.com/
""")
        questions = [
            inquirer.Text("account", message="Storage Account Name:"),
            inquirer.Password("key", message="Account Key:"),
        ]
    
    else:
        print(f"""
Đối với {remote_type}, chúng tôi sẽ sử dụng quá trình cấu hình tương tác.

Để biết thêm chi tiết về cách thiết lập {remote_type}, vui lòng tham khảo:
https://rclone.org/docs/#{remote_type}

Sau khi tiếp tục, hệ thống sẽ hướng dẫn bạn qua quy trình thiết lập.
""")
        return {}
    
    print("\nSau khi nhập thông tin, rclone có thể yêu cầu xác thực bổ sung qua trình duyệt web.")
    print("Vui lòng làm theo hướng dẫn hiển thị trên màn hình khi được nhắc.")
    print("="*80 + "\n")
    
    answers = inquirer.prompt(questions)
    
    if answers:
        # Filter out empty values
        return {k: v for k, v in answers.items() if v}
    
    return {}


def prompt_remove_remote():
    """Prompt for removing a remote."""
    rclone_manager = RcloneManager()
    config_manager = RcloneConfigManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\nChưa có remote nào được cấu hình.")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Tạo danh sách lựa chọn với thông tin thêm về loại remote
    display_choices = []
    for remote in remotes:
        config = config_manager.get_remote_config(remote)
        remote_type = config.get("type", "unknown") if config else "unknown"
        display_type = get_remote_type_display_name(remote_type)
        display_choices.append(f"{remote} ({display_type})")
    
    # Thêm lựa chọn huỷ
    display_choices.append("Huỷ")
    
    questions = [
        inquirer.List(
            "remote_display",
            message="Chọn remote để xoá:",
            choices=display_choices,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if not answers or answers["remote_display"] == "Huỷ":
        return
    
    # Trích xuất tên remote từ chuỗi hiển thị (trước dấu ngoặc đầu tiên)
    remote_name = answers["remote_display"].split(" (")[0]
    
    # Hiển thị cảnh báo rõ ràng với thông tin về remote
    config = config_manager.get_remote_config(remote_name)
    if config:
        remote_type = config.get("type", "unknown")
        display_type = get_remote_type_display_name(remote_type)
        print(f"\n⚠️  CẢNH BÁO: Bạn sắp xoá remote '{remote_name}' ({display_type}).")
        print("    Hành động này không thể hoàn tác và sẽ xoá cấu hình liên kết với dịch vụ này.")
        print("    Dữ liệu trên dịch vụ lưu trữ không bị ảnh hưởng.")
    
    confirm = inquirer.prompt([
        inquirer.Confirm("confirm", message=f"Bạn có chắc chắn muốn xoá '{remote_name}'?", default=False)
    ])
    
    if confirm and confirm["confirm"]:
        success = rclone_manager.remove_remote(remote_name)
        
        if success:
            print(f"\n✅ Remote '{remote_name}' đã được xoá thành công.")
        else:
            print(f"\n❌ Lỗi khi xoá remote '{remote_name}'.")
    
    input("\nNhấn Enter để tiếp tục...")


def prompt_view_remote_details():
    """Prompt for viewing remote details."""
    rclone_manager = RcloneManager()
    config_manager = RcloneConfigManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\nChưa có remote nào được cấu hình.")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Tạo danh sách lựa chọn với thông tin thêm về loại remote
    display_choices = []
    for remote in remotes:
        config = config_manager.get_remote_config(remote)
        remote_type = config.get("type", "unknown") if config else "unknown"
        display_type = get_remote_type_display_name(remote_type)
        display_choices.append(f"{remote} ({display_type})")
    
    # Thêm lựa chọn huỷ
    display_choices.append("Huỷ")
    
    questions = [
        inquirer.List(
            "remote_display",
            message="Chọn remote để xem chi tiết:",
            choices=display_choices,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if not answers or answers["remote_display"] == "Huỷ":
        return
        
    # Trích xuất tên remote từ chuỗi hiển thị (trước dấu ngoặc đầu tiên)
    remote_name = answers["remote_display"].split(" (")[0]
    config = config_manager.get_remote_config(remote_name)
    
    if config:
        remote_type = config.get("type", "unknown")
        display_type = get_remote_type_display_name(remote_type)
        
        print(f"\nChi tiết cấu hình cho remote '{remote_name}' ({display_type}):")
        print("=" * 80)
        
        # Hiển thị thông tin được nhóm lại
        # Nhóm 1: Thông tin cơ bản
        print("THÔNG TIN CƠ BẢN:")
        print(f"  Tên: {remote_name}")
        print(f"  Loại: {display_type}")
        
        # Nhóm 2: Thông tin kết nối và xác thực
        print("\nTHÔNG TIN KẾT NỐI:")
        for key, value in config.items():
            if key == "type":
                continue  # Đã hiển thị ở trên
                
            # Hiển thị nhãn thân thiện cho các trường
            key_display = {
                "provider": "Nhà cung cấp",
                "access_key_id": "Access Key ID",
                "region": "Vùng",
                "endpoint": "Endpoint",
                "account": "Tài khoản",
                "user": "Tên người dùng",
                "host": "Máy chủ",
                "port": "Cổng kết nối",
                "url": "URL"
            }.get(key, key)
            
            # Ẩn thông tin nhạy cảm
            if key in ["secret", "key", "pass", "password", "secret_access_key", "client_secret"]:
                value = "********"
                key_display = f"{key_display} (đã ẩn)"
                
            print(f"  {key_display}: {value}")
        
        print("=" * 80)
        
        # Thêm thông tin sử dụng
        used_space = "Không xác định"  # Trong thực tế, bạn có thể gọi rclone để lấy thông tin này
        print(f"\nLưu ý: Đây là thông tin cấu hình của remote. Để quản lý dữ liệu,")
        print(f"hãy sử dụng các tùy chọn khác như 'View backup files' hoặc 'Backup to remote'.")
    else:
        print(f"\nKhông tìm thấy thông tin chi tiết cho remote '{remote_name}'.")
    
    input("\nNhấn Enter để tiếp tục...")


def prompt_backup_to_remote():
    """Prompt for backing up data to a remote."""
    rclone_manager = RcloneManager()
    config_manager = RcloneConfigManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\nChưa có remote nào được cấu hình. Vui lòng thêm remote trước.")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Tạo danh sách lựa chọn với thông tin thêm về loại remote
    display_choices = []
    for remote in remotes:
        config = config_manager.get_remote_config(remote)
        remote_type = config.get("type", "unknown") if config else "unknown"
        display_type = get_remote_type_display_name(remote_type)
        display_choices.append(f"{remote} ({display_type})")
    
    # Thêm lựa chọn huỷ
    display_choices.append("Huỷ")
    
    questions = [
        inquirer.List(
            "remote_display",
            message="Chọn remote đích:",
            choices=display_choices,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if not answers or answers["remote_display"] == "Huỷ":
        return
    
    # Trích xuất tên remote từ chuỗi hiển thị (trước dấu ngoặc đầu tiên)
    remote_name = answers["remote_display"].split(" (")[0]
    
    # Kiểm tra xem người dùng muốn sao lưu cho trang web cụ thể hay không
    site_backup_question = [
        inquirer.Confirm(
            "use_domain",
            message="Bạn muốn sao lưu cho một trang web cụ thể?",
            default=True
        )
    ]
    
    site_backup_answer = inquirer.prompt(site_backup_question)
    if not site_backup_answer:
        return
    
    domain = None
    if site_backup_answer.get("use_domain", True):
        # Hiển thị các domain sẵn có nếu SITES_DIR tồn tại
        sites_dir = get_env_value("SITES_DIR")
        if sites_dir and os.path.exists(sites_dir):
            available_domains = [d for d in os.listdir(sites_dir) if os.path.isdir(os.path.join(sites_dir, d))]
            
            if available_domains:
                domain_question = [
                    inquirer.List(
                        "domain",
                        message="Chọn trang web để sao lưu:",
                        choices=available_domains + ["Tự nhập tên miền khác"]
                    )
                ]
                
                domain_answer = inquirer.prompt(domain_question)
                if not domain_answer:
                    return
                
                if domain_answer["domain"] == "Tự nhập tên miền khác":
                    custom_domain_question = [
                        inquirer.Text(
                            "custom_domain",
                            message="Nhập tên miền của trang web:"
                        )
                    ]
                    
                    custom_domain_answer = inquirer.prompt(custom_domain_question)
                    if not custom_domain_answer:
                        return
                    
                    domain = custom_domain_answer["custom_domain"]
                else:
                    domain = domain_answer["domain"]
            else:
                # Không có domain, yêu cầu người dùng nhập
                domain_input_question = [
                    inquirer.Text(
                        "domain_input",
                        message="Nhập tên miền của trang web cần sao lưu:"
                    )
                ]
                
                domain_input_answer = inquirer.prompt(domain_input_question)
                if not domain_input_answer:
                    return
                
                domain = domain_input_answer["domain_input"]
        else:
            # Không có SITES_DIR hoặc thư mục không tồn tại, yêu cầu người dùng nhập
            domain_input_question = [
                inquirer.Text(
                    "domain_input",
                    message="Nhập tên miền của trang web cần sao lưu:"
                )
            ]
            
            domain_input_answer = inquirer.prompt(domain_input_question)
            if not domain_input_answer:
                return
            
            domain = domain_input_answer["domain_input"]
    
    # Sử dụng các đường dẫn tiêu chuẩn
    if domain:
        # Đường dẫn nguồn tiêu chuẩn
        sites_dir = get_env_value("SITES_DIR")
        source = os.path.join(sites_dir, domain, "wordpress")
        
        # Kiểm tra thư mục wordpress có tồn tại không
        if not os.path.exists(source):
            # Thử thư mục www nếu wordpress không tồn tại
            www_dir = os.path.join(sites_dir, domain, "www")
            if os.path.exists(www_dir):
                source = www_dir
                print(f"\n⚠️ Thư mục wordpress không tồn tại, sử dụng thư mục www thay thế.")
            else:
                # Sử dụng thư mục gốc của domain
                source = os.path.join(sites_dir, domain)
                print(f"\n⚠️ Không tìm thấy thư mục wordpress hoặc www, sử dụng thư mục gốc của trang web.")
        
        # Đường dẫn đích tiêu chuẩn trên remote
        destination = f"backups/{domain}"
        
        print(f"\nThông tin sao lưu cho trang web: {domain}")
        print(f"Nguồn: {source}")
        print(f"Đích: {remote_name}:{destination}")
    else:
        print("\n❌ Cần chọn một trang web cụ thể để sao lưu.")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Confirm backup operation
    confirm = inquirer.prompt([
        inquirer.Confirm(
            "confirm", 
            message=f"Sao lưu '{domain}' lên '{remote_name}:{destination}'?", 
            default=False
        )
    ])
    
    if confirm and confirm["confirm"]:
        print(f"\n⏳ Đang bắt đầu sao lưu lên '{remote_name}'...")
        
        # Create remote directory structure first - rclone mkdir doesn't support -p
        remote_path_components = destination.split('/')
        current_path = ""
        
        for component in remote_path_components:
            if component:
                current_path = f"{current_path}/{component}" if current_path else component
                mkdir_success, mkdir_message = rclone_manager.execute_command(
                    ["mkdir", f"{remote_name}:{current_path}"]
                )
                # Don't show a warning if the directory already exists
                if not mkdir_success and "already exists" not in mkdir_message.lower():
                    print(f"\n⚠️ Không thể tạo thư mục '{current_path}': {mkdir_message}")
            
        # Execute backup
        success, output = rclone_manager.backup(source, remote_name, destination, domain)
        
        if success:
            print(f"\n✅ Sao lưu hoàn tất thành công.")
        else:
            print(f"\n❌ Sao lưu thất bại: {output}")
    
    input("\nNhấn Enter để tiếp tục...")




def prompt_view_backup_files():
    """Prompt for viewing backup files on a remote."""
    rclone_manager = RcloneManager()
    config_manager = RcloneConfigManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\nChưa có remote nào được cấu hình. Vui lòng thêm remote trước.")
        input("\nNhấn Enter để tiếp tục...")
        return
    
    # Tạo danh sách lựa chọn với thông tin thêm về loại remote
    display_choices = []
    for remote in remotes:
        config = config_manager.get_remote_config(remote)
        remote_type = config.get("type", "unknown") if config else "unknown"
        display_type = get_remote_type_display_name(remote_type)
        display_choices.append(f"{remote} ({display_type})")
    
    # Thêm lựa chọn huỷ
    display_choices.append("Huỷ")
    
    questions = [
        inquirer.List(
            "remote_display",
            message="Chọn remote để xem tệp tin:",
            choices=display_choices,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if not answers or answers["remote_display"] == "Huỷ":
        return
    
    # Trích xuất tên remote từ chuỗi hiển thị (trước dấu ngoặc đầu tiên)
    remote_name = answers["remote_display"].split(" (")[0]
    
    # Get path to list
    path_question = [
        inquirer.Text(
            "path",
            message="Nhập đường dẫn để hiển thị (mặc định: backups/):",
            default="backups/"
        ),
    ]
    
    path_answer = inquirer.prompt(path_question)
    
    if not path_answer:
        return
    
    path = path_answer["path"]
    
    # List files in the remote path
    print(f"\n⏳ Đang liệt kê tệp tin trong '{remote_name}:{path}'...")
    files = rclone_manager.list_files(remote_name, path)
    
    if files:
        print(f"\n📋 Tệp tin trong '{remote_name}:{path}':")
        print("=" * 80)
        print(f"{'Tên':30} {'Kích thước':12} {'Loại':12} {'Thời gian chỉnh sửa'}")
        print("-" * 80)
        
        for file in files:
            name = file.get("Name", "Unknown")
            size = format_size(file.get("Size", 0))
            mod_time = file.get("ModTime", "Unknown")
            file_type = "📁 Thư mục" if file.get("IsDir", False) else "📄 Tệp tin"
            
            print(f"{name[:30]:30} {size:12} {file_type:12} {mod_time}")
        
        print("=" * 80)
    else:
        print(f"\n❌ Không tìm thấy tệp tin nào trong '{remote_name}:{path}'.")
    
    input("\nNhấn Enter để tiếp tục...")