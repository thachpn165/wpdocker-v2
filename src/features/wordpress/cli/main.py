"""
Main CLI entry point for WordPress management.

This module provides a centralized command-line interface for all WordPress
management operations, including installation and command execution.
"""

import sys
import argparse
from typing import List, Optional

from src.common.logging import log_call, info, warn, error, success
from src.features.wordpress.cli.install import cli_install_wordpress
from src.features.wordpress.cli.manage import cli_run_wp_command, cli_uninstall_wordpress
from src.features.wordpress.cli.protect import cli_toggle_wp_login_protection
from src.features.wordpress.utils import show_wp_user_list, reset_wp_user_password, get_wp_user_info


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the WordPress CLI.

    Args:
        args: Command-line arguments

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="WordPress management CLI",
        prog="wordpress"
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="WordPress management commands"
    )

    # Install WordPress
    install_parser = subparsers.add_parser(
        "install",
        help="Install WordPress on a website"
    )

    # Run WP-CLI command
    wp_parser = subparsers.add_parser(
        "wp",
        help="Run WP-CLI commands"
    )

    # Uninstall WordPress
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Completely remove WordPress from a website"
    )

    # Protect wp-login.php
    protect_parser = subparsers.add_parser(
        "protect",
        help="Toggle wp-login.php protection with HTTP Basic Authentication"
    )
    protect_parser.add_argument(
        "domain",
        nargs="?",
        help="Website domain (if omitted, will prompt to select)"
    )

    # Reset Admin Password
    reset_pw_parser = subparsers.add_parser(
        "reset-admin-password",
        help="Reset mật khẩu cho user WordPress (hiển thị mật khẩu mới)"
    )
    reset_pw_parser.add_argument(
        "domain",
        nargs="?",
        help="Website domain (nếu bỏ trống sẽ chọn từ danh sách)"
    )

    return parser.parse_args(args)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the WordPress CLI.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_args(args)

    if not parsed_args.command:
        # No command specified, show help
        parse_args(["--help"])
        return 1

    if parsed_args.command == "install":
        return 0 if cli_install_wordpress() else 1

    elif parsed_args.command == "wp":
        return 0 if cli_run_wp_command() else 1

    elif parsed_args.command == "uninstall":
        return 0 if cli_uninstall_wordpress() else 1

    elif parsed_args.command == "protect":
        return 0 if cli_toggle_wp_login_protection(parsed_args.domain) else 1

    elif parsed_args.command == "reset-admin-password":
        return 0 if cli_reset_admin_password(parsed_args.domain) else 1

    else:
        error(f"Unknown command: {parsed_args.command}")
        return 1


def cli_reset_admin_password(domain: Optional[str] = None):
    from src.features.website.utils import select_website
    from src.common.logging import info, error, success
    if not domain:
        domain = select_website("Chọn website cần reset mật khẩu admin:")
        if not domain:
            info("Không có website nào hoặc thao tác bị hủy.")
            return False
    show_wp_user_list(domain)
    user_id = input("Nhập user ID cần reset mật khẩu: ").strip()
    if not user_id.isdigit():
        error("User ID không hợp lệ.")
        return False
    new_password = reset_wp_user_password(domain, user_id)
    if new_password:
        user_info = get_wp_user_info(domain, user_id)
        username = user_info[
            "user_login"] if user_info and "user_login" in user_info else f"user_id={user_id}"
        success(
            f"✅ Đã reset mật khẩu cho {username} (user id = {user_id}) trên {domain}")
        info(f"👤 Tên người dùng: {username}")
        info(f"🔑 Mật khẩu mới: {new_password}")
        info("Hãy lưu lại mật khẩu này và đổi lại sau khi đăng nhập.")
        return True
    else:
        error("❌ Không thể reset mật khẩu.")
        return False


if __name__ == "__main__":
    sys.exit(main())
