import hashlib
import os
import re
from typing import List, Tuple
from datetime import datetime


def calculate_md5(file_path: str) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        return ""


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"


def parse_search_keywords(keyword: str) -> List[str]:
    """Parse search keywords separated by |"""
    return [k.strip() for k in keyword.split("|") if k.strip()]


def is_apk_file(filename: str) -> bool:
    """Check if file is an APK file"""
    return filename.lower().endswith('.apk')


def extract_build_type(filename: str) -> str:
    """Extract build type from file name"""
    filename_lower = filename.lower()
    if 'release' in filename_lower:
        return 'release'
    elif 'debug' in filename_lower:
        return 'debug'
    return 'unknown'


def safe_path_join(*paths) -> str:
    """Safely join paths with proper separators"""
    return os.path.join(*paths).replace('\\', '/')


def validate_smb_path(path: str) -> bool:
    """Validate SMB path format"""
    pattern = r'^\\\\[\w.-]+\\[\w\s.-]+.*$'
    return bool(re.match(pattern, path))


def parse_interval(interval_str: str) -> int:
    """Parse interval string like '5m', '1h' to seconds"""
    if not interval_str:
        return 300  # default 5 minutes
    
    unit = interval_str[-1].lower()
    try:
        value = int(interval_str[:-1])
    except ValueError:
        return 300
    
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    else:
        return 300