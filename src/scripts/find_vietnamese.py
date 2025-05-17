#!/usr/bin/env python3
"""
Script to find Vietnamese text in source code files.
This helps identify text that needs to be translated to English.
"""

import os
import re
import argparse
from pathlib import Path
import unicodedata

def is_vietnamese(text):
    """Check if text contains Vietnamese characters."""
    # Vietnamese specific characters
    vietnamese_chars = set('áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ')
    
    for char in text:
        if char in vietnamese_chars:
            return True
    
    return False

def scan_file(file_path):
    """Scan a file for Vietnamese text."""
    results = []
    
    # Skip binary files
    if not os.path.isfile(file_path) or os.path.getsize(file_path) > 1024 * 1024:  # Skip files > 1MB
        return results
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if is_vietnamese(line):
                    # Clean up the line
                    clean_line = line.strip()
                    results.append((i, clean_line))
    except UnicodeDecodeError:
        # Skip files that can't be decoded as UTF-8
        pass
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return results

def scan_directory(directory, extensions=None, exclude_dirs=None):
    """Recursively scan directory for files with Vietnamese text."""
    if exclude_dirs is None:
        exclude_dirs = ['.git', 'node_modules', '__pycache__', 'venv', 'env', '.venv', '.env']
    
    if extensions is None:
        extensions = ['.py', '.sh', '.md', '.txt', '.yml', '.yaml', '.json', '.template']
    
    results = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            if extensions and file_ext not in extensions:
                continue
            
            file_results = scan_file(file_path)
            if file_results:
                results[file_path] = file_results
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Find Vietnamese text in code files')
    parser.add_argument('directory', help='Directory to scan', default='.', nargs='?')
    parser.add_argument('--extensions', help='File extensions to scan (comma separated)', default='.py,.sh,.md,.txt,.yml,.yaml,.json,.template')
    parser.add_argument('--exclude', help='Directories to exclude (comma separated)', default='.git,node_modules,__pycache__,venv,env,.venv,.env')
    
    args = parser.parse_args()
    
    directory = os.path.abspath(args.directory)
    extensions = [ext.strip() if ext.strip().startswith('.') else f'.{ext.strip()}' for ext in args.extensions.split(',')]
    exclude_dirs = [dir.strip() for dir in args.exclude.split(',')]
    
    print(f"Scanning directory: {directory}")
    print(f"File extensions: {', '.join(extensions)}")
    print(f"Excluded directories: {', '.join(exclude_dirs)}")
    print("-" * 80)
    
    results = scan_directory(directory, extensions, exclude_dirs)
    
    if not results:
        print("No Vietnamese text found.")
        return
    
    total_files = len(results)
    total_occurrences = sum(len(occurrences) for occurrences in results.values())
    
    print(f"Found {total_occurrences} occurrences of Vietnamese text in {total_files} files:")
    print()
    
    for file_path, occurrences in results.items():
        rel_path = os.path.relpath(file_path, directory)
        print(f"\033[1m{rel_path}\033[0m:")
        
        for line_num, line in occurrences:
            print(f"  Line {line_num}: {line}")
        
        print()

if __name__ == "__main__":
    main()