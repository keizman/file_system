import os
import tempfile
import uuid
from datetime import datetime
from typing import List, Dict, Tuple
from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, CreateDisposition, CreateOptions, FileAttributes, ShareAccess, ImpersonationLevel
from smbprotocol.query_info import FileInformationClass
from loguru import logger
from shared.models import APKFile
from shared.utils import is_apk_file, extract_build_type

def extract_smb_file_name(entry) -> str:
    """
    Extract file name from SMB directory entry using smbprotocol's structure access.
    
    Args:
        entry: SMB directory entry object (FileDirectoryInformation)
        
    Returns:
        str: Decoded file name or None if extraction fails
    """
    try:
        # Based on smbprotocol's structure, we need to access fields using dictionary-style access
        # The correct way is: entry['field_name'].value
        
        # Method 1: Dictionary-style access with .value attribute (recommended approach)
        try:
            file_name_bytes = entry['file_name'].value
            if isinstance(file_name_bytes, bytes) and len(file_name_bytes) > 0:
                file_name = file_name_bytes.decode('utf-16le').rstrip('\x00')
                return file_name.strip() if file_name else None
        except Exception:
            pass
        
        # Method 2: Alternative attribute access
        try:
            if hasattr(entry, 'file_name'):
                file_name_field = entry.file_name
                if hasattr(file_name_field, 'value'):
                    file_name_bytes = file_name_field.value
                    if isinstance(file_name_bytes, bytes) and len(file_name_bytes) > 0:
                        file_name = file_name_bytes.decode('utf-16le').rstrip('\x00')
                        return file_name.strip() if file_name else None
        except Exception:
            pass
        
        # Method 3: Try with get_value() method
        try:
            if hasattr(entry, 'file_name'):
                file_name_field = entry.file_name
                if hasattr(file_name_field, 'get_value'):
                    file_name_bytes = file_name_field.get_value()
                    if isinstance(file_name_bytes, bytes) and len(file_name_bytes) > 0:
                        file_name = file_name_bytes.decode('utf-16le').rstrip('\x00')
                        return file_name.strip() if file_name else None
        except Exception:
            pass
        
        # Method 4: Raw data extraction as fallback
        try:
            # Get file name length first
            file_name_length = None
            if hasattr(entry, 'file_name_length'):
                length_field = entry.file_name_length
                if hasattr(length_field, 'value'):
                    file_name_length = length_field.value
                elif hasattr(length_field, 'get_value'):
                    file_name_length = length_field.get_value()
            
            # Try dictionary access for length
            if file_name_length is None:
                try:
                    file_name_length = entry['file_name_length'].value
                except:
                    pass
            
            if file_name_length and file_name_length > 0:
                # Extract from packed data
                packed_data = entry.pack()
                if len(packed_data) >= file_name_length:
                    file_name_bytes = packed_data[-file_name_length:]
                    if isinstance(file_name_bytes, bytes) and len(file_name_bytes) > 0:
                        file_name = file_name_bytes.decode('utf-16le').rstrip('\x00')
                        return file_name.strip() if file_name else None
        except Exception:
            pass
        
        return None
            
    except Exception as e:
        logger.error(f"Error extracting file name: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return None


class SMBClient:
    def __init__(self, server_config: Dict):
        self.server_config = server_config
        self.connection = None
        self.session = None
        self.tree = None
        self.server_name = server_config.get("name", "Unknown")
        self.host = None
        self.share = None
        self.username = server_config.get("username", "")
        self.password = server_config.get("password", "")
    
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
            
            # Store host and share for later use
            self.host = server_ip
            self.share = share_name
            
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
            dir_open.create(
                desired_access=0x00000001,  # FILE_READ_DATA
                file_attributes=FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE,
                create_disposition=CreateDisposition.FILE_OPEN,
                create_options=CreateOptions.FILE_DIRECTORY_FILE,
                impersonation_level=ImpersonationLevel.Impersonation
            )
            
            # Query directory contents - try different information classes
            entries = None
            for info_class in [FileInformationClass.FILE_DIRECTORY_INFORMATION, 
                              FileInformationClass.FILE_FULL_DIRECTORY_INFORMATION,
                              FileInformationClass.FILE_BOTH_DIRECTORY_INFORMATION]:
                try:
                    logger.debug(f"Trying FileInformationClass: {info_class}")
                    entries = dir_open.query_directory("*", info_class)
                    logger.debug(f"Successfully got {len(entries)} entries with {info_class}")
                    break
                except Exception as e:
                    logger.debug(f"Failed with {info_class}: {e}")
            
            if entries is None:
                logger.error("Could not query directory with any FileInformationClass")
                return directories
            
            for entry in entries:
                # Get file name from FileDirectoryInformation
                file_name = extract_smb_file_name(entry)
                
                if file_name is None or file_name in [".", ".."]:
                    logger.debug(f"Skipping entry with invalid file name: {file_name}")
                    continue
                
                # Additional validation for file name
                if not file_name or file_name.strip() == "":
                    logger.debug(f"Skipping entry with empty file name")
                    continue
                
                # Get file attributes from FileDirectoryInformation
                file_attrs = None
                
                try:
                    # Try dictionary access first
                    file_attrs = entry['file_attributes'].value
                except Exception:
                    try:
                        # Fallback to attribute access
                        if hasattr(entry, 'file_attributes'):
                            file_attrs_field = entry.file_attributes
                            if hasattr(file_attrs_field, 'value'):
                                file_attrs = file_attrs_field.value
                            else:
                                file_attrs = file_attrs_field
                    except Exception:
                        pass
                
                if file_attrs is None:
                    logger.debug(f"Could not find file attributes for entry: {file_name}")
                    continue
                    
                if file_attrs & FileAttributes.FILE_ATTRIBUTE_DIRECTORY:
                    if file_name not in [".", ".."]:
                        directories.append(file_name)
            
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
            dir_open.create(
                desired_access=0x00000001,  # FILE_READ_DATA
                file_attributes=FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE,
                create_disposition=CreateDisposition.FILE_OPEN,
                create_options=CreateOptions.FILE_DIRECTORY_FILE,
                impersonation_level=ImpersonationLevel.Impersonation
            )
            
            # Query directory contents - try different information classes
            entries = None
            for info_class in [FileInformationClass.FILE_DIRECTORY_INFORMATION, 
                              FileInformationClass.FILE_FULL_DIRECTORY_INFORMATION,
                              FileInformationClass.FILE_BOTH_DIRECTORY_INFORMATION]:
                try:
                    entries = dir_open.query_directory("*", info_class)
                    break
                except Exception as e:
                    logger.debug(f"Failed with {info_class}: {e}")
            
            if entries is None:
                logger.error("Could not query directory with any FileInformationClass")
                return
            
            for entry in entries:
                # Get file name from FileDirectoryInformation
                file_name = extract_smb_file_name(entry)
                
                if file_name is None or file_name in [".", ".."]:
                    continue
                
                # Additional validation for file name
                if not file_name or file_name.strip() == "":
                    continue
                
                entry_path = f"{path}\\{file_name}" if path else file_name
                
                # Get file attributes from FileDirectoryInformation
                file_attrs = None
                
                try:
                    # Try dictionary access first
                    file_attrs = entry['file_attributes'].value
                except Exception:
                    try:
                        # Fallback to attribute access
                        if hasattr(entry, 'file_attributes'):
                            file_attrs_field = entry.file_attributes
                            if hasattr(file_attrs_field, 'value'):
                                file_attrs = file_attrs_field.value
                            else:
                                file_attrs = file_attrs_field
                    except Exception:
                        pass
                
                if file_attrs is None:
                    continue
                    
                if file_attrs & FileAttributes.FILE_ATTRIBUTE_DIRECTORY:
                    # Recursively scan subdirectory
                    self._scan_directory_recursive(entry_path, apk_files, base_dir)
                elif is_apk_file(file_name):
                    # Create APK file object
                    file_size = None
                    creation_time = None
                    
                    try:
                        # Get file size
                        try:
                            file_size = entry['end_of_file'].value
                        except Exception:
                            if hasattr(entry, 'end_of_file'):
                                size_field = entry.end_of_file
                                file_size = size_field.value if hasattr(size_field, 'value') else size_field
                        
                        # Get creation time
                        try:
                            creation_time = entry['creation_time'].value
                        except Exception:
                            if hasattr(entry, 'creation_time'):
                                time_field = entry.creation_time
                                creation_time = time_field.value if hasattr(time_field, 'value') else time_field
                            
                    except Exception as e:
                        logger.debug(f"Error getting file info: {e}")
                    
                    if file_size is not None and creation_time is not None:
                        apk_file = APKFile(
                            relative_path=f"\\{entry_path}",
                            file_name=file_name,
                            file_size=file_size,
                            created_time=datetime.fromtimestamp(creation_time.timestamp()),
                            server_prefix=self.server_config["path"],
                            build_type=extract_build_type(file_name),
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
            file_open.create(
                desired_access=0x00000001,  # FILE_READ_DATA
                file_attributes=FileAttributes.FILE_ATTRIBUTE_NORMAL,
                share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE,
                create_disposition=CreateDisposition.FILE_OPEN,
                create_options=CreateOptions.FILE_NON_DIRECTORY_FILE,
                impersonation_level=ImpersonationLevel.Impersonation
            )
            
            # Get file size to prevent reading past end
            try:
                # Use the correct smbprotocol API to get file information
                from smbprotocol.file_info import FileInformationClass
                file_info_data = file_open.query_info(
                    info_type=1,  # FileInfoType.SMB2_0_INFO_FILE
                    file_info_class=FileInformationClass.FILE_STANDARD_INFORMATION,
                    output_buffer_length=4096
                )
                # Parse the file standard information to get file size
                if file_info_data and len(file_info_data) >= 24:  # FILE_STANDARD_INFORMATION is 24 bytes
                    import struct
                    # Bytes 16-24 contain the EndOfFile (file size)
                    file_size = struct.unpack('<Q', file_info_data[16:24])[0]
                    logger.debug(f"Got file size using query_info: {file_size}")
                else:
                    file_size = None
                    logger.debug("Could not get file size using query_info")
            except (AttributeError, Exception) as e:
                logger.debug(f"Could not get file size using query_info: {e}")
                # Fallback: try to read file size from initial read
                try:
                    # Try a small read to determine if file is accessible
                    test_data = file_open.read(0, 1)
                    if test_data:
                        # File is accessible, but we don't know the size
                        # Use a conservative approach: read until EOF
                        file_size = None
                        logger.debug("File accessible, but size unknown - will read until EOF")
                    else:
                        logger.error("File appears to be empty or inaccessible")
                        return False
                except Exception as e:
                    logger.error(f"Cannot determine file size: {e}")
                    return False
            
            # Create local directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file in chunks
            with open(local_path, 'wb') as local_file:
                offset = 0
                chunk_size = 65536  # 64KB chunks
                
                if file_size is not None:
                    # We know the file size, use it to prevent reading past end
                    while offset < file_size:
                        # Calculate how much to read (don't read past end of file)
                        bytes_to_read = min(chunk_size, file_size - offset)
                        
                        try:
                            data = file_open.read(offset, bytes_to_read)
                            if not data:
                                break
                            local_file.write(data)
                            offset += len(data)
                        except Exception as read_error:
                            # Handle STATUS_END_OF_FILE and other read errors
                            if "STATUS_END_OF_FILE" in str(read_error):
                                logger.debug(f"Reached end of file at offset {offset}/{file_size}")
                                break
                            else:
                                raise read_error
                else:
                    # We don't know the file size, read until EOF
                    while True:
                        try:
                            data = file_open.read(offset, chunk_size)
                            if not data:
                                break
                            local_file.write(data)
                            offset += len(data)
                        except Exception as read_error:
                            # Handle STATUS_END_OF_FILE and other read errors
                            if "STATUS_END_OF_FILE" in str(read_error):
                                logger.debug(f"Reached end of file at offset {offset}")
                                break
                            else:
                                raise read_error
            
            file_open.close()
            if file_size is not None:
                logger.info(f"Downloaded file: {relative_path} -> {local_path} ({file_size} bytes)")
            else:
                logger.info(f"Downloaded file: {relative_path} -> {local_path} ({offset} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file {relative_path}: {e}")
            return False
    
    def download_file_stream(self, relative_path: str):
        """Download a file from SMB server as a stream with progress"""
        try:
            if not self.tree:
                raise Exception("Not connected to SMB server")
            
            # Build remote path
            base_path = self.server_config["path"].split("\\")[-1]
            remote_path = f"{base_path}{relative_path}"
            
            # Open remote file
            file_open = Open(self.tree, remote_path)
            file_open.create(
                desired_access=0x00000001,  # FILE_READ_DATA
                file_attributes=FileAttributes.FILE_ATTRIBUTE_NORMAL,
                share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE,
                create_disposition=CreateDisposition.FILE_OPEN,
                create_options=CreateOptions.FILE_NON_DIRECTORY_FILE,
                impersonation_level=ImpersonationLevel.Impersonation
            )
            
            # Get file size to prevent reading past end
            try:
                # Use the correct smbprotocol API to get file information
                from smbprotocol.file_info import FileInformationClass
                file_info = file_open.query_info(
                    info_type=1,  # FileInfoType.SMB2_0_INFO_FILE
                    file_info_class=FileInformationClass.FILE_STANDARD_INFORMATION,
                    output_buffer_length=4096
                )
                # Parse the file standard information to get file size
                if file_info and len(file_info) >= 24:  # FILE_STANDARD_INFORMATION is 24 bytes
                    import struct
                    # Bytes 16-24 contain the EndOfFile (file size)
                    file_size = struct.unpack('<Q', file_info[16:24])[0]
                    logger.debug(f"Got file size using query_info: {file_size}")
                else:
                    file_size = None
                    logger.debug("Could not get file size using query_info")
            except (AttributeError, Exception) as e:
                logger.debug(f"Could not get file size using query_info: {e}")
                # Fallback: try to read file size from initial read
                try:
                    # Try a small read to determine if file is accessible
                    test_data = file_open.read(0, 1)
                    if test_data:
                        # File is accessible, but we don't know the size
                        # Use a conservative approach: read until EOF
                        file_size = None
                        logger.debug("File accessible, but size unknown - will read until EOF")
                    else:
                        logger.error("File appears to be empty or inaccessible")
                        file_open.close()
                        raise Exception("File appears to be empty or inaccessible")
                except Exception as e:
                    file_open.close()
                    logger.error(f"Cannot determine file size: {e}")
                    raise Exception(f"Cannot determine file size: {e}")
            
            # Generator function to yield file chunks
            def generate_chunks():
                offset = 0
                chunk_size = 65536  # 64KB chunks
                
                try:
                    if file_size is not None:
                        # We know the file size, use it to prevent reading past end
                        while offset < file_size:
                            # Calculate how much to read (don't read past end of file)
                            bytes_to_read = min(chunk_size, file_size - offset)
                            
                            try:
                                data = file_open.read(offset, bytes_to_read)
                                if not data:
                                    break
                                yield data
                                offset += len(data)
                            except Exception as read_error:
                                # Handle STATUS_END_OF_FILE and other read errors
                                if "STATUS_END_OF_FILE" in str(read_error):
                                    logger.debug(f"Reached end of file at offset {offset}/{file_size}")
                                    break
                                else:
                                    raise read_error
                    else:
                        # We don't know the file size, read until EOF
                        while True:
                            try:
                                data = file_open.read(offset, chunk_size)
                                if not data:
                                    break
                                yield data
                                offset += len(data)
                            except Exception as read_error:
                                # Handle STATUS_END_OF_FILE and other read errors
                                if "STATUS_END_OF_FILE" in str(read_error):
                                    logger.debug(f"Reached end of file at offset {offset}")
                                    break
                                else:
                                    raise read_error
                finally:
                    file_open.close()
                    if file_size is not None:
                        logger.info(f"Streamed file: {relative_path} ({file_size} bytes)")
                    else:
                        logger.info(f"Streamed file: {relative_path} ({offset} bytes)")
            
            return generate_chunks(), file_size
            
        except Exception as e:
            logger.error(f"Error streaming file {relative_path}: {e}")
            raise
    
    def download_file_stream_simple(self, path: str):
        """
        简化版文件下载流，跳过文件大小获取以避免SMB协议兼容性问题
        
        Args:
            path: 文件路径
            
        Returns:
            tuple: (file_stream_generator, None) - 文件大小始终为None
        """
        logger.info(f"Starting simplified file stream download: {path}")
        
        if not self.tree:
            logger.error("Not connected to SMB server")
            raise Exception("Not connected to SMB server")
        
        # Normalize path
        if path.startswith('\\'):
            path = path[1:]
        normalized_path = path.replace('/', '\\')
        
        logger.debug(f"Downloading file from normalized path: {normalized_path}")
        
        # Open file for reading
        file_open = Open(self.tree, normalized_path)
        try:
            file_open.create(
                ImpersonationLevel.Impersonation,
                FileAttributes.FILE_ATTRIBUTE_NORMAL | FileAttributes.FILE_ATTRIBUTE_ARCHIVE,
                ShareAccess.FILE_SHARE_READ,
                CreateDisposition.FILE_OPEN,
                CreateOptions.FILE_NON_DIRECTORY_FILE
            )
            
            logger.debug("File opened successfully - creating stream generator")
            
            def file_stream():
                offset = 0
                chunk_size = 64 * 1024  # 64KB chunks to avoid credit issues
                
                try:
                    while True:
                        try:
                            data = file_open.read(offset, chunk_size)
                            if not data:
                                logger.debug(f"Reached end of file at offset {offset}")
                                break
                            
                            logger.debug(f"Read {len(data)} bytes at offset {offset}")
                            yield data
                            offset += len(data)
                            
                        except Exception as e:
                            logger.error(f"Error reading file at offset {offset}: {e}")
                            break
                            
                finally:
                    logger.debug("Closing file handle")
                    file_open.close()
            
            return file_stream(), None  # Always return None for file size
            
        except Exception as e:
            logger.error(f"Error opening file {normalized_path}: {e}")
            try:
                file_open.close()
            except:
                pass
            raise
    
    def download_file_stream_smbclient(self, path: str):
        """
        使用smbclient高级API下载文件，更稳定可靠
        
        Args:
            path: 文件路径
            
        Returns:
            tuple: (file_stream_generator, file_size)
        """
        logger.info(f"Starting smbclient download: {path}")
        logger.debug(f"Server config path: {self.server_config['path']}")
        
        # Parse server config to get the complete UNC path
        server_path = self.server_config["path"]  # e.g., \\192.168.1.37\yw\apks
        
        # Construct full UNC path by combining server config path with requested path
        if server_path.endswith("\\"):
            server_path = server_path[:-1]  # Remove trailing backslash
        
        if path.startswith("\\"):
            unc_path = f"{server_path}{path}"
        else:
            unc_path = f"{server_path}\\{path}"
        
        logger.debug(f"Constructed UNC path: {unc_path}")
        
        try:
            import smbclient
            import time
            import random
            from smbprotocol.exceptions import SMBOSError
            
            # Configure credentials with connection settings for better reliability
            smbclient.ClientConfig(
                username=self.username,
                password=self.password,
                connection_timeout=30,
                auth_protocol="ntlm"
            )
            
            def file_stream_with_retry():
                max_retries = 3
                base_delay = 0.1
                
                for attempt in range(max_retries + 1):
                    try:
                        # Check if file is accessible before opening
                        if not self._is_file_accessible(unc_path):
                            if attempt < max_retries:
                                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                                logger.warning(f"File not accessible, retry {attempt + 1}/{max_retries} after {delay:.2f}s")
                                time.sleep(delay)
                                continue
                            else:
                                raise Exception("File is locked or not accessible after all retries")
                        
                        with smbclient.open_file(unc_path, mode='rb', buffering=0, 
                                               timeout=30, share_access=['r', 'w', 'd']) as f:
                            chunk_size = 64 * 1024  # 64KB chunks
                            chunks_read = 0
                            
                            while True:
                                try:
                                    data = f.read(chunk_size)
                                    if not data:
                                        break
                                    chunks_read += 1
                                    yield data
                                except Exception as read_error:
                                    logger.error(f"Error reading chunk {chunks_read}: {read_error}")
                                    if "being used by another process" in str(read_error):
                                        raise  # Let outer retry handle this
                                    raise
                        
                        logger.info(f"Successfully streamed file after {attempt + 1} attempt(s)")
                        return
                        
                    except SMBOSError as e:
                        if "0xc0000043" in str(e) or "being used by another process" in str(e):
                            if attempt < max_retries:
                                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                                logger.warning(f"File locked, retry {attempt + 1}/{max_retries} after {delay:.2f}s: {e}")
                                time.sleep(delay)
                                continue
                            else:
                                logger.error(f"File permanently locked after {max_retries} retries: {e}")
                                # Try fallback method
                                yield from self._fallback_file_copy(unc_path)
                                return
                        else:
                            logger.error(f"SMB error (non-retry): {e}")
                            raise
                    except Exception as e:
                        if attempt < max_retries and ("timeout" in str(e).lower() or "connection" in str(e).lower()):
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                            logger.warning(f"Connection error, retry {attempt + 1}/{max_retries} after {delay:.2f}s: {e}")
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(f"Error reading file with smbclient: {e}")
                            raise
                
                raise Exception("Max retries exceeded")
            
            # Don't call stat here to avoid file locking issues
            # File size will be determined by API layer using separate stat call
            file_size = None
            
            return file_stream_with_retry(), file_size
            
        except ImportError:
            logger.error("smbclient high-level API not available, falling back to low-level API")
            return self.download_file_stream_simple(path)
        except Exception as e:
            logger.error(f"smbclient download failed: {e}")
            raise
    
    def _is_file_accessible(self, unc_path: str) -> bool:
        """
        Check if a file is accessible without holding a lock
        
        Args:
            unc_path: Full UNC path to the file
            
        Returns:
            bool: True if file is accessible, False otherwise
        """
        try:
            import smbclient
            from smbprotocol.exceptions import SMBOSError
            
            # Quick stat check - if this fails, file is likely locked
            stat_info = smbclient.stat(unc_path)
            return stat_info.st_size > 0
            
        except SMBOSError as e:
            if "0xc0000043" in str(e) or "being used by another process" in str(e):
                logger.debug(f"File accessibility check failed - file is locked: {unc_path}")
                return False
            logger.debug(f"File accessibility check failed with SMB error: {e}")
            return False
        except Exception as e:
            logger.debug(f"File accessibility check failed with error: {e}")
            return False
    
    def _fallback_file_copy(self, unc_path: str):
        """
        Fallback method: copy file to temp location and stream from there
        
        Args:
            unc_path: Full UNC path to the file
            
        Yields:
            bytes: File chunks
        """
        import tempfile
        import os
        import shutil
        
        temp_file = None
        try:
            logger.info(f"Attempting fallback file copy for: {unc_path}")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.apk')
            temp_path = temp_file.name
            temp_file.close()
            
            # Try to copy file using different methods
            success = False
            
            # Method 1: Try smbclient with different share access
            try:
                import smbclient
                smbclient.copyfile(unc_path, temp_path, timeout=60)
                success = True
                logger.info(f"Fallback copy successful using smbclient.copyfile")
            except Exception as e:
                logger.warning(f"Fallback method 1 failed: {e}")
            
            # Method 2: Try with system commands as last resort
            if not success:
                try:
                    import subprocess
                    # Use smbget on Linux systems
                    if os.name != 'nt':
                        # Extract server info for smbget
                        server_parts = unc_path.split('\\')
                        if len(server_parts) >= 4:
                            server = server_parts[2]
                            share = server_parts[3]
                            file_path = '\\'.join(server_parts[4:])
                            smb_url = f"smb://{server}/{share}/{file_path.replace('\\', '/')}"
                            
                            cmd = ['smbget', '-U', f'{self.username}%{self.password}', 
                                  smb_url, '-o', temp_path]
                            subprocess.run(cmd, check=True, timeout=60)
                            success = True
                            logger.info(f"Fallback copy successful using smbget")
                except Exception as e:
                    logger.warning(f"Fallback method 2 failed: {e}")
            
            if not success:
                raise Exception("All fallback copy methods failed")
            
            # Stream from temporary file
            with open(temp_path, 'rb') as f:
                chunk_size = 64 * 1024
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data
                    
        except Exception as e:
            logger.error(f"Fallback file copy failed: {e}")
            raise
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                    logger.debug(f"Cleaned up temporary file: {temp_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
    
    def download_file_range_stream(self, path: str, start: int, end: int):
        """
        下载文件的指定范围，支持断点续传
        
        Args:
            path: 文件路径
            start: 开始字节位置
            end: 结束字节位置 (包含)
            
        Returns:
            generator: 文件流生成器
        """
        logger.info(f"Starting range download: {path} [{start}-{end}]")
        
        # Try smbclient first if available
        try:
            import smbclient
            
            # Configure credentials if not already done
            smbclient.ClientConfig(
                username=self.username,
                password=self.password
            )
            
            # Construct full UNC path
            if path.startswith('\\'):
                path = path[1:]
            unc_path = f"\\\\{self.host}\\{self.share}\\{path}"
            
            def range_stream():
                try:
                    with smbclient.open_file(unc_path, mode='rb', buffering=0) as f:
                        # Seek to start position
                        f.seek(start)
                        
                        remaining = end - start + 1
                        chunk_size = min(64 * 1024, remaining)  # 64KB chunks or remaining bytes
                        
                        while remaining > 0:
                            bytes_to_read = min(chunk_size, remaining)
                            data = f.read(bytes_to_read)
                            if not data:
                                break
                            yield data
                            remaining -= len(data)
                            
                except Exception as e:
                    logger.error(f"Error reading range with smbclient: {e}")
                    raise
            
            return range_stream()
            
        except ImportError:
            logger.error("smbclient not available for range download")
            raise Exception("smbclient required for range downloads")
        except Exception as e:
            logger.error(f"Range download with smbclient failed: {e}")
            # Fall back to low-level API
            return self._download_range_low_level(path, start, end)
    
    def _download_range_low_level(self, path: str, start: int, end: int):
        """
        使用低级API下载文件范围
        """
        if not self.tree:
            raise Exception("SMB connection not established")
        
        base_path = self.server_config["path"].split("\\")[-1]
        remote_path = f"{base_path}{path}"
        
        file_open = Open(self.tree, remote_path)
        
        try:
            file_open.create(
                desired_access=0x00000001,  # FILE_READ_DATA
                file_attributes=FileAttributes.FILE_ATTRIBUTE_NORMAL,
                share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE,
                create_disposition=CreateDisposition.FILE_OPEN,
                create_options=CreateOptions.FILE_NON_DIRECTORY_FILE,
                impersonation_level=ImpersonationLevel.Impersonation
            )
            
            def range_stream():
                try:
                    offset = start
                    remaining = end - start + 1
                    chunk_size = min(65536, remaining)  # 64KB chunks
                    
                    while remaining > 0 and offset <= end:
                        bytes_to_read = min(chunk_size, remaining)
                        
                        try:
                            data = file_open.read(offset, bytes_to_read)
                            if not data:
                                break
                            yield data
                            offset += len(data)
                            remaining -= len(data)
                        except Exception as read_error:
                            if "STATUS_END_OF_FILE" in str(read_error):
                                logger.debug(f"Reached end of file at offset {offset}")
                                break
                            else:
                                raise read_error
                                
                finally:
                    file_open.close()
                    logger.info(f"Range download completed: {path} [{start}-{end}]")
            
            return range_stream()
            
        except Exception as e:
            logger.error(f"Error in range download {path}: {e}")
            try:
                file_open.close()
            except:
                pass
            raise
    
    def download_file_stream_with_skip(self, path: str, start: int, end: int):
        """
        下载文件并跳过到指定位置（当范围下载不可用时的后备方案）
        """
        logger.warning(f"Using skip method for range download: {path} [{start}-{end}]")
        
        # Get normal file stream
        try:
            file_stream, _ = self.download_file_stream_smbclient(path)
        except:
            file_stream, _ = self.download_file_stream(path)
        
        def skip_stream():
            bytes_skipped = 0
            bytes_served = 0
            target_bytes = end - start + 1
            
            for chunk in file_stream:
                if bytes_skipped < start:
                    # Still skipping to start position
                    skip_in_chunk = min(len(chunk), start - bytes_skipped)
                    bytes_skipped += skip_in_chunk
                    
                    if bytes_skipped >= start:
                        # Start serving from this chunk
                        serve_from = skip_in_chunk
                        remaining_in_chunk = len(chunk) - serve_from
                        bytes_to_serve = min(remaining_in_chunk, target_bytes - bytes_served)
                        
                        if bytes_to_serve > 0:
                            yield chunk[serve_from:serve_from + bytes_to_serve]
                            bytes_served += bytes_to_serve
                            
                        if bytes_served >= target_bytes:
                            break
                else:
                    # Already at serving position
                    bytes_to_serve = min(len(chunk), target_bytes - bytes_served)
                    if bytes_to_serve > 0:
                        yield chunk[:bytes_to_serve]
                        bytes_served += bytes_to_serve
                        
                    if bytes_served >= target_bytes:
                        break
        
        return skip_stream()
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists on SMB server"""
        try:
            if not self.tree:
                return False
            
            base_path = self.server_config["path"].split("\\")[-1]
            remote_path = f"{base_path}{relative_path}"
            
            file_open = Open(self.tree, remote_path)
            try:
                file_open.create(
                    desired_access=0x00000001,  # FILE_READ_DATA
                    file_attributes=FileAttributes.FILE_ATTRIBUTE_NORMAL,
                    share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE,
                    create_disposition=CreateDisposition.FILE_OPEN,
                    create_options=CreateOptions.FILE_NON_DIRECTORY_FILE,
                    impersonation_level=ImpersonationLevel.Impersonation
                )
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
            file_open.create(
                desired_access=0x00000001,  # FILE_READ_DATA
                file_attributes=FileAttributes.FILE_ATTRIBUTE_NORMAL,
                share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE | ShareAccess.FILE_SHARE_DELETE,
                create_disposition=CreateDisposition.FILE_OPEN,
                create_options=CreateOptions.FILE_NON_DIRECTORY_FILE,
                impersonation_level=ImpersonationLevel.Impersonation
            )
            
            # Get file information using correct smbprotocol API
            try:
                from smbprotocol.file_info import FileInformationClass
                file_info_data = file_open.query_info(
                    info_type=1,  # FileInfoType.SMB2_0_INFO_FILE
                    file_info_class=FileInformationClass.FILE_STANDARD_INFORMATION,
                    output_buffer_length=4096
                )
                
                if file_info_data and len(file_info_data) >= 24:
                    import struct
                    # Parse FILE_STANDARD_INFORMATION structure
                    # Bytes 16-24: EndOfFile (file size)
                    file_size = struct.unpack('<Q', file_info_data[16:24])[0]
                    
                    # For timestamps, we need a different query
                    try:
                        basic_info_data = file_open.query_info(
                            info_type=1,
                            file_info_class=FileInformationClass.FILE_BASIC_INFORMATION,
                            output_buffer_length=4096
                        )
                        if basic_info_data and len(basic_info_data) >= 40:
                            # Parse FILE_BASIC_INFORMATION structure
                            creation_time = struct.unpack('<Q', basic_info_data[0:8])[0]
                            last_write_time = struct.unpack('<Q', basic_info_data[24:32])[0]
                            
                            # Convert Windows FILETIME to Unix timestamp
                            # FILETIME is 100-nanosecond intervals since January 1, 1601
                            unix_epoch_delta = 116444736000000000  # 100-ns intervals between 1601 and 1970
                            creation_timestamp = (creation_time - unix_epoch_delta) / 10000000
                            modified_timestamp = (last_write_time - unix_epoch_delta) / 10000000
                            
                            file_info = {
                                "size": file_size,
                                "created_time": datetime.fromtimestamp(creation_timestamp),
                                "modified_time": datetime.fromtimestamp(modified_timestamp),
                                "exists": True
                            }
                        else:
                            # Fallback without timestamps
                            file_info = {
                                "size": file_size,
                                "created_time": datetime.now(),
                                "modified_time": datetime.now(),
                                "exists": True
                            }
                    except Exception:
                        # Fallback without timestamps
                        file_info = {
                            "size": file_size,
                            "created_time": datetime.now(),
                            "modified_time": datetime.now(),
                            "exists": True
                        }
                else:
                    # Fallback: file exists but can't get detailed info
                    file_info = {
                        "size": 0,
                        "created_time": datetime.now(),
                        "modified_time": datetime.now(),
                        "exists": True
                    }
            except Exception as e:
                logger.warning(f"Could not get detailed file info, using fallback: {e}")
                # Fallback: file exists but can't get detailed info
                file_info = {
                    "size": 0,
                    "created_time": datetime.now(),
                    "modified_time": datetime.now(),
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
            from .config import Config
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