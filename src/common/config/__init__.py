"""
Module cấu hình hệ thống.

Module này cung cấp các lớp và công cụ cho việc quản lý cấu hình hệ thống.
"""

# Sử dụng try-except để tương thích với cả hai cách import
try:
    # Import tương đối khi src đã được cài đặt như một package
    from src.common.config.manager import ConfigManager
except ImportError:
    # Import tương đối trong package khi chạy trực tiếp
    from .manager import ConfigManager