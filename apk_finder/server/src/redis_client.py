import json
import redis
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from shared.models import APKFile
from config import Config


class RedisClient:
    def __init__(self):
        self.client = None
        self.connect()
    
    def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(Config.REDIS_CONN_STRING)
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def get_apk_files(self, server_name: str, directory: str) -> List[APKFile]:
        """Get APK files for a specific directory"""
        key = f"apk_finder:{server_name}:{directory}"
        try:
            data = self.client.hget(key, "files")
            if data:
                files_data = json.loads(data)
                return [APKFile(**file_data) for file_data in files_data]
            return []
        except Exception as e:
            logger.error(f"Error getting APK files for {key}: {e}")
            return []
    
    def set_apk_files(self, server_name: str, directory: str, files: List[APKFile]):
        """Set APK files for a specific directory"""
        key = f"apk_finder:{server_name}:{directory}"
        try:
            files_data = [file.model_dump() for file in files]
            self.client.hset(key, "files", json.dumps(files_data, default=str))
            self.client.hset(key, "last_updated", datetime.now().isoformat())
            logger.debug(f"Updated {len(files)} APK files for {key}")
        except Exception as e:
            logger.error(f"Error setting APK files for {key}: {e}")
    
    def get_directory_meta(self, server_name: str, directory: str) -> Optional[Dict]:
        """Get metadata for a directory"""
        key = f"apk_finder:{server_name}:meta"
        try:
            data = self.client.hget(key, directory)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting directory meta for {directory}: {e}")
            return None
    
    def set_directory_meta(self, server_name: str, directory: str, meta: Dict):
        """Set metadata for a directory"""
        key = f"apk_finder:{server_name}:meta"
        try:
            self.client.hset(key, directory, json.dumps(meta, default=str))
            logger.debug(f"Updated meta for {server_name}:{directory}")
        except Exception as e:
            logger.error(f"Error setting directory meta for {directory}: {e}")
    
    def search_apk_files(self, keyword: str, server: Optional[str] = None, 
                        build_type: str = "release", limit: int = 10, 
                        offset: int = 0) -> tuple[List[APKFile], int]:
        """Search for APK files"""
        try:
            all_files = []
            
            # Determine which servers to search
            servers_to_search = [server] if server else Config.FILE_SERVERS.keys()
            
            for server_name in servers_to_search:
                # Get all directories for this server
                pattern = f"apk_finder:{server_name}:*"
                keys = self.client.keys(pattern)
                
                for key in keys:
                    if key.decode().endswith(':meta'):
                        continue
                    
                    directory = key.decode().split(':')[-1]
                    files = self.get_apk_files(server_name, directory)
                    all_files.extend(files)
            
            # Filter files
            filtered_files = self._filter_files(all_files, keyword, build_type)
            
            # Sort by created_time descending
            filtered_files.sort(key=lambda x: x.created_time, reverse=True)
            
            # Apply pagination
            total = len(filtered_files)
            paginated_files = filtered_files[offset:offset + limit]
            
            return paginated_files, total
            
        except Exception as e:
            logger.error(f"Error searching APK files: {e}")
            return [], 0
    
    def _filter_files(self, files: List[APKFile], keyword: str, build_type: str) -> List[APKFile]:
        """Filter files by keyword and build type"""
        filtered = []
        
        # Parse keywords (support multiple keywords separated by |)
        keywords = [k.strip().lower() for k in keyword.split("|") if k.strip()]
        
        for file in files:
            # Filter by build type
            if build_type != "combine":
                if file.build_type != build_type:
                    continue
            
            # Filter by keywords
            if keywords:
                file_text = f"{file.file_name} {file.relative_path}".lower()
                if not all(kw in file_text for kw in keywords):
                    continue
            
            filtered.append(file)
        
        return filtered
    
    def get_system_status(self) -> Dict:
        """Get system status information"""
        try:
            status = {
                "redis_connected": True,
                "total_servers": len(Config.FILE_SERVERS),
                "total_files": 0,
                "last_scan_time": None,
                "servers_status": {}
            }
            
            # Get total files count and server status
            for server_name in Config.FILE_SERVERS.keys():
                server_files = 0
                last_scan = None
                
                pattern = f"apk_finder:{server_name}:*"
                keys = self.client.keys(pattern)
                
                for key in keys:
                    if key.decode().endswith(':meta'):
                        continue
                    
                    directory = key.decode().split(':')[-1]
                    files = self.get_apk_files(server_name, directory)
                    server_files += len(files)
                    
                    # Get last updated time
                    last_updated = self.client.hget(key, "last_updated")
                    if last_updated:
                        scan_time = datetime.fromisoformat(last_updated.decode())
                        if not last_scan or scan_time > last_scan:
                            last_scan = scan_time
                
                status["servers_status"][server_name] = {
                    "files_count": server_files,
                    "last_scan": last_scan.isoformat() if last_scan else None
                }
                status["total_files"] += server_files
                
                if last_scan and (not status["last_scan_time"] or last_scan > datetime.fromisoformat(status["last_scan_time"])):
                    status["last_scan_time"] = last_scan.isoformat()
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"redis_connected": False, "error": str(e)}
    
    def increment_download_count(self, server_name: str, directory: str, file_path: str):
        """Increment download count for a file"""
        try:
            files = self.get_apk_files(server_name, directory)
            for file in files:
                if file.relative_path == file_path:
                    file.download_time += 1
                    break
            self.set_apk_files(server_name, directory, files)
        except Exception as e:
            logger.error(f"Error incrementing download count: {e}")
    
    def update_file_md5(self, server_name: str, directory: str, file_path: str, md5: str):
        """Update MD5 hash for a file"""
        try:
            files = self.get_apk_files(server_name, directory)
            for file in files:
                if file.relative_path == file_path:
                    file.md5 = md5
                    break
            self.set_apk_files(server_name, directory, files)
        except Exception as e:
            logger.error(f"Error updating file MD5: {e}")


# Global Redis client instance
redis_client = RedisClient()