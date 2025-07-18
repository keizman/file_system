import os
import tempfile
from datetime import datetime
from typing import List, Dict, Tuple
from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, CreateDisposition, CreateOptions, FileAttributes
from smbprotocol.query_info import QueryInfoRequest, FileInformation
from loguru import logger
from shared.models import APKFile
from shared.utils import is_apk_file, extract_build_type


class SMBClient:
    def __init__(self, server_config: Dict):
        self.server_config = server_config
        self.connection = None
        self.session = None
        self.tree = None
        self.server_name = server_config.get("name", "Unknown")
    
    def connect(self) -> bool:
        """Connect to SMB server"""
        try:
            # Parse server path
            server_path = self.server_config["path"]
            if not server_path.startswith("\\\\"):
                logger.error(f"Invalid SMB path format: {server_path}")
                return False
            
            parts = server_path.replace("\\", "/").split("/")
            server_ip = parts[2]
            share_name = parts[3] if len(parts) > 3 else "C$"
            
            # Create connection
            self.connection = Connection(uuid.uuid4(), server_ip, 445)
            self.connection.connect()
            
            # Create session
            self.session = Session(self.connection, 
                                 self.server_config["username"], 
                                 self.server_config["password"])
            self.session.connect()
            
            # Connect to tree (share)
            self.tree = TreeConnect(self.session, f"\\\\{server_ip}\\{share_name}")
            self.tree.connect()
            
            logger.info(f"Connected to SMB server: {server_ip}\\{share_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SMB server {self.server_name}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from SMB server"""
        try:
            if self.tree:
                self.tree.disconnect()
            if self.session:
                self.session.disconnect()
            if self.connection:
                self.connection.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from SMB server: {e}")
    
    def list_directories(self, path: str = "") -> List[str]:
        """List directories in the given path"""
        try:
            if not self.tree:
                return []
            
            # Build full path
            base_path = self.server_config["path"].split("\\")[-1]  # Get the last part after share
            if base_path and not path.startswith(base_path):
                full_path = f"{base_path}\\{path}" if path else base_path
            else:
                full_path = path
            
            directories = []
            
            # Open directory for listing
            dir_open = Open(self.tree, full_path)
            dir_open.create(CreateDisposition.FILE_OPEN,
                          CreateOptions.FILE_DIRECTORY_FILE,
                          FileAttributes.FILE_ATTRIBUTE_DIRECTORY)
            
            # Query directory contents
            query_req = QueryInfoRequest()
            query_req.info_type = FileInformation.FILE_DIRECTORY_INFORMATION
            
            entries = dir_open.query_directory("*")
            
            for entry in entries:
                if entry.file_attributes & FileAttributes.FILE_ATTRIBUTE_DIRECTORY:
                    if entry.file_name not in [".", ".."]:
                        directories.append(entry.file_name)
            
            dir_open.close()
            return directories
            
        except Exception as e:
            logger.error(f"Error listing directories in {path}: {e}")
            return []
    
    def get_directory_file_count(self, path: str) -> int:
        """Get the number of subdirectories in a directory"""
        try:
            subdirs = self.list_directories(path)
            return len(subdirs)
        except Exception as e:
            logger.error(f"Error getting directory count for {path}: {e}")
            return 0
    
    def scan_apk_files(self, directory: str) -> List[APKFile]:
        """Recursively scan for APK files in a directory"""
        apk_files = []
        try:
            self._scan_directory_recursive(directory, apk_files, directory)
        except Exception as e:
            logger.error(f"Error scanning APK files in {directory}: {e}")
        
        return apk_files
    
    def _scan_directory_recursive(self, path: str, apk_files: List[APKFile], base_dir: str):
        """Recursively scan directory for APK files"""
        try:
            if not self.tree:
                return
            
            # Build full path
            base_path = self.server_config["path"].split("\\")[-1]
            full_path = f"{base_path}\\{path}" if path else base_path
            
            # Open directory
            dir_open = Open(self.tree, full_path)
            dir_open.create(CreateDisposition.FILE_OPEN,
                          CreateOptions.FILE_DIRECTORY_FILE,
                          FileAttributes.FILE_ATTRIBUTE_DIRECTORY)
            
            entries = dir_open.query_directory("*")
            
            for entry in entries:
                if entry.file_name in [".", ".."]:
                    continue
                
                entry_path = f"{path}\\{entry.file_name}" if path else entry.file_name
                
                if entry.file_attributes & FileAttributes.FILE_ATTRIBUTE_DIRECTORY:
                    # Recursively scan subdirectory
                    self._scan_directory_recursive(entry_path, apk_files, base_dir)
                elif is_apk_file(entry.file_name):
                    # Create APK file object
                    apk_file = APKFile(
                        relative_path=f"\\{entry_path}",
                        file_name=entry.file_name,
                        file_size=entry.end_of_file,
                        created_time=datetime.fromtimestamp(entry.creation_time.timestamp()),
                        server_prefix=self.server_config["path"],
                        build_type=extract_build_type(entry_path),
                        download_time=0,
                        md5=None
                    )
                    apk_files.append(apk_file)
            
            dir_open.close()
            
        except Exception as e:
            logger.error(f"Error scanning directory {path}: {e}")
    
    def download_file(self, relative_path: str, local_path: str) -> bool:
        """Download a file from SMB server to local path"""
        try:
            if not self.tree:
                return False
            
            # Build remote path
            base_path = self.server_config["path"].split("\\")[-1]
            remote_path = f"{base_path}{relative_path}"
            
            # Open remote file
            file_open = Open(self.tree, remote_path)
            file_open.create(CreateDisposition.FILE_OPEN,
                           CreateOptions.FILE_NON_DIRECTORY_FILE,
                           FileAttributes.FILE_ATTRIBUTE_NORMAL)
            
            # Create local directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file in chunks
            with open(local_path, 'wb') as local_file:
                offset = 0
                chunk_size = 65536  # 64KB chunks
                
                while True:
                    data = file_open.read(offset, chunk_size)
                    if not data:
                        break
                    local_file.write(data)
                    offset += len(data)
            
            file_open.close()
            logger.info(f"Downloaded file: {relative_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file {relative_path}: {e}")
            return False
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists on SMB server"""
        try:
            if not self.tree:
                return False
            
            base_path = self.server_config["path"].split("\\")[-1]
            remote_path = f"{base_path}{relative_path}"
            
            file_open = Open(self.tree, remote_path)
            try:
                file_open.create(CreateDisposition.FILE_OPEN,
                               CreateOptions.FILE_NON_DIRECTORY_FILE,
                               FileAttributes.FILE_ATTRIBUTE_NORMAL)
                file_open.close()
                return True
            except:
                return False
                
        except Exception as e:
            logger.error(f"Error checking file existence {relative_path}: {e}")
            return False
    
    def get_file_info(self, relative_path: str) -> Dict:
        """Get file information"""
        try:
            if not self.tree:
                return {}
            
            base_path = self.server_config["path"].split("\\")[-1]
            remote_path = f"{base_path}{relative_path}"
            
            file_open = Open(self.tree, remote_path)
            file_open.create(CreateDisposition.FILE_OPEN,
                           CreateOptions.FILE_NON_DIRECTORY_FILE,
                           FileAttributes.FILE_ATTRIBUTE_NORMAL)
            
            # Get file information
            info = file_open.query_info()
            
            file_info = {
                "size": info.end_of_file,
                "created_time": datetime.fromtimestamp(info.creation_time.timestamp()),
                "modified_time": datetime.fromtimestamp(info.last_write_time.timestamp()),
                "exists": True
            }
            
            file_open.close()
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info for {relative_path}: {e}")
            return {"exists": False}


class SMBManager:
    def __init__(self):
        self.clients = {}
    
    def get_client(self, server_name: str) -> SMBClient:
        """Get or create SMB client for server"""
        if server_name not in self.clients:
            from config import Config
            if server_name not in Config.FILE_SERVERS:
                raise ValueError(f"Unknown server: {server_name}")
            
            client = SMBClient(Config.FILE_SERVERS[server_name])
            if client.connect():
                self.clients[server_name] = client
            else:
                raise ConnectionError(f"Failed to connect to server: {server_name}")
        
        return self.clients[server_name]
    
    def disconnect_all(self):
        """Disconnect all SMB clients"""
        for client in self.clients.values():
            client.disconnect()
        self.clients.clear()


# Global SMB manager instance
smb_manager = SMBManager()