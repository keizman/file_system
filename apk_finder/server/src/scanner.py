import asyncio
import threading
from datetime import datetime
from typing import Dict, List
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from config import Config
from redis_client import redis_client
from smb_client import smb_manager
from shared.models import APKFile


class APKScanner:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scanning = False
        self.scan_lock = threading.Lock()
    
    def start(self):
        """Start the scanner service"""
        logger.info("Starting APK scanner service")
        
        # Schedule periodic scans
        self.scheduler.add_job(
            func=self.scan_all_servers,
            trigger="interval",
            seconds=Config.UPDATE_INTERVAL,
            id="periodic_scan",
            replace_existing=True
        )
        
        # Schedule temp file cleanup
        self.scheduler.add_job(
            func=self.cleanup_temp_files,
            trigger="interval",
            seconds=Config.TEMP_CLEAN_INTERVAL,
            id="temp_cleanup",
            replace_existing=True
        )
        
        self.scheduler.start()
        
        # Perform initial scan
        threading.Thread(target=self.scan_all_servers, daemon=True).start()
    
    def stop(self):
        """Stop the scanner service"""
        logger.info("Stopping APK scanner service")
        self.scheduler.shutdown()
        smb_manager.disconnect_all()
    
    def scan_all_servers(self):
        """Scan all configured servers"""
        if self.scanning:
            logger.info("Scan already in progress, skipping")
            return
        
        with self.scan_lock:
            self.scanning = True
            logger.info("Starting scan of all servers")
            
            try:
                for server_name, server_config in Config.FILE_SERVERS.items():
                    logger.info(f"Scanning server: {server_name}")
                    self.scan_server(server_name)
                    
                logger.info("Completed scan of all servers")
                
            except Exception as e:
                logger.error(f"Error during server scan: {e}")
            finally:
                self.scanning = False
    
    def scan_server(self, server_name: str):
        """Scan a specific server for APK files"""
        try:
            client = smb_manager.get_client(server_name)
            
            # Get top-level directories (second-level directories in the design)
            directories = client.list_directories("")
            logger.info(f"Found {len(directories)} directories in {server_name}")
            
            for directory in directories:
                try:
                    self.scan_directory(server_name, directory, client)
                except Exception as e:
                    logger.error(f"Error scanning directory {directory}: {e}")
                    continue
            
            logger.info(f"Completed scanning server: {server_name}")
            
        except Exception as e:
            logger.error(f"Error connecting to server {server_name}: {e}")
    
    def scan_directory(self, server_name: str, directory: str, client):
        """Scan a specific directory using incremental algorithm"""
        try:
            # Get current subdirectory count
            current_count = client.get_directory_file_count(directory)
            
            # Get cached count from Redis
            cached_meta = redis_client.get_directory_meta(server_name, directory)
            cached_count = cached_meta.get("subdir_count", -1) if cached_meta else -1
            
            logger.debug(f"Directory {directory}: current={current_count}, cached={cached_count}")
            
            # Check if scan is needed
            if current_count == cached_count and cached_count != -1:
                logger.debug(f"Skipping {directory} - no changes detected")
                return
            
            logger.info(f"Scanning directory {directory} - changes detected or first scan")
            
            # Scan for APK files
            apk_files = client.scan_apk_files(directory)
            
            # Update Redis with new data
            redis_client.set_apk_files(server_name, directory, apk_files)
            
            # Update metadata
            meta = {
                "subdir_count": current_count,
                "last_scan": datetime.now().isoformat(),
                "files_count": len(apk_files)
            }
            redis_client.set_directory_meta(server_name, directory, meta)
            
            logger.info(f"Updated {directory}: {len(apk_files)} APK files found")
            
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    def force_scan_server(self, server_name: str):
        """Force a complete scan of a specific server"""
        if server_name not in Config.FILE_SERVERS:
            raise ValueError(f"Unknown server: {server_name}")
        
        logger.info(f"Force scanning server: {server_name}")
        
        # Clear cached metadata to force rescan
        try:
            client = smb_manager.get_client(server_name)
            directories = client.list_directories("")
            
            for directory in directories:
                # Clear cached metadata
                redis_client.set_directory_meta(server_name, directory, {"subdir_count": -1})
            
            # Perform scan
            self.scan_server(server_name)
            
        except Exception as e:
            logger.error(f"Error force scanning server {server_name}: {e}")
            raise
    
    def force_scan_all(self):
        """Force a complete scan of all servers"""
        logger.info("Force scanning all servers")
        
        # Clear all cached metadata
        for server_name in Config.FILE_SERVERS.keys():
            try:
                client = smb_manager.get_client(server_name)
                directories = client.list_directories("")
                
                for directory in directories:
                    redis_client.set_directory_meta(server_name, directory, {"subdir_count": -1})
                    
            except Exception as e:
                logger.error(f"Error clearing cache for server {server_name}: {e}")
        
        # Perform scan
        self.scan_all_servers()
    
    def cleanup_temp_files(self):
        """Clean up old temporary files"""
        try:
            import os
            import time
            
            temp_dir = Config.TEMP_DIR
            if not os.path.exists(temp_dir):
                return
            
            current_time = time.time()
            max_age = 3600  # 1 hour
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age:
                        try:
                            os.remove(file_path)
                            logger.debug(f"Removed old temp file: {filename}")
                        except Exception as e:
                            logger.error(f"Error removing temp file {filename}: {e}")
            
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")
    
    def get_scan_status(self) -> Dict:
        """Get current scan status"""
        return {
            "scanning": self.scanning,
            "scheduler_running": self.scheduler.running,
            "next_scan_time": self.scheduler.get_job("periodic_scan").next_run_time.isoformat() if self.scheduler.get_job("periodic_scan") else None
        }


# Global scanner instance
scanner = APKScanner()