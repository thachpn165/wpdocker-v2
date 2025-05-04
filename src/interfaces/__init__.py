#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package chứa các lớp trừu tượng và interface cho toàn bộ hệ thống.

Các lớp trong package này định nghĩa giao diện chuẩn mà các lớp thực thi cụ thể 
phải tuân theo, giúp đảm bảo tính mở rộng và khả năng bảo trì.
"""

from src.interfaces.AbstractPrompt import AbstractPrompt
from src.interfaces.AbstractPHPExtension import AbstractPHPExtension
from src.interfaces.IStorageProvider import IStorageProvider

__all__ = [
    'AbstractPrompt',
    'AbstractPHPExtension',
    'IStorageProvider'
]