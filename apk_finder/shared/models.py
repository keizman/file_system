from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class APKFile(BaseModel):
    relative_path: str
    file_name: str
    file_size: int
    created_time: datetime
    server_prefix: str
    build_type: str  # release/debug
    download_time: int = 0
    md5: Optional[str] = None


class SearchRequest(BaseModel):
    keyword: str
    server: Optional[str] = None
    build_type: str = "release"  # release/debug/combine
    limit: int = 10
    offset: int = 0


class SearchResponse(BaseModel):
    code: int
    data: dict


class SystemStatus(BaseModel):
    last_scan_time: Optional[datetime]
    total_files: int
    scanning: bool
    servers_status: dict
    redis_status: str


class DownloadRequest(BaseModel):
    path: str
    server: str


class FileInfo(BaseModel):
    path: str
    size: int
    modified_time: datetime
    md5: Optional[str] = None
    exists: bool