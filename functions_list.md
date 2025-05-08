## SSL Utils
- get_ssl_paths(domain): Lấy đường dẫn các file SSL cho domain
- ensure_ssl_dir(domain): Đảm bảo thư mục SSL tồn tại
- backup_ssl_files(domain): Backup các file SSL
- has_ssl_certificate(domain): Kiểm tra domain đã có SSL chưa
- restore_ssl_backup(domain, backup_path): Khôi phục backup SSL 