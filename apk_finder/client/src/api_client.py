import httpx
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from shared.models import SearchRequest, APKFile
from config import ClientConfig


class APIClient:
    def __init__(self):
        self.base_url = ClientConfig.SERVER_URL
        self.headers = {
            "Authorization": f"Bearer {ClientConfig.API_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def search_apk_files(self, keyword: str, server: Optional[str] = None, 
                              build_type: str = "release", limit: int = 10, 
                              offset: int = 0) -> Tuple[List[Dict], int]:
        """Search for APK files"""
        try:
            request_data = SearchRequest(
                keyword=keyword,
                server=server,
                build_type=build_type,
                limit=limit,
                offset=offset
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/search",
                    headers=self.headers,
                    json=request_data.model_dump()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["data"]["items"], data["data"]["total"]
                else:
                    print(f"Search failed: {response.status_code} - {response.text}")
                    return [], 0
                    
        except Exception as e:
            print(f"Error searching APK files: {e}")
            return [], 0
    
    async def refresh_scan(self, server: Optional[str] = None) -> bool:
        """Trigger server refresh scan"""
        try:
            params = {"server": server} if server else {}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/refresh",
                    headers=self.headers,
                    params=params
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"Error triggering refresh: {e}")
            return False
    
    async def get_download_url(self, path: str, server: str) -> str:
        """Get download URL for a file"""
        params = {
            "path": path,
            "server": server
        }
        
        # Build URL with query parameters
        url = f"{self.base_url}/api/download"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        return f"{url}?{query_string}"
    
    async def download_file(self, path: str, server: str, local_path: str, 
                           progress_callback=None) -> bool:
        """Download file from server"""
        try:
            params = {
                "path": path,
                "server": server
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "GET",
                    f"{self.base_url}/api/download",
                    headers=self.headers,
                    params=params
                ) as response:
                    
                    if response.status_code != 200:
                        print(f"Download failed: {response.status_code}")
                        return False
                    
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    
                    with open(local_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                progress_callback(progress)
                    
                    return True
                    
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
    
    async def get_file_info(self, path: str, server: str) -> Optional[Dict]:
        """Get file information"""
        try:
            params = {
                "path": path,
                "server": server
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/file/info",
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            print(f"Error getting file info: {e}")
            return None
    
    async def get_system_status(self) -> Optional[Dict]:
        """Get system status"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/status",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            print(f"Error getting system status: {e}")
            return None
    
    async def get_servers(self) -> List[Dict]:
        """Get list of available servers"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/servers",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["data"]
                else:
                    return []
                    
        except Exception as e:
            print(f"Error getting servers: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
                
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


# Global API client instance
api_client = APIClient()