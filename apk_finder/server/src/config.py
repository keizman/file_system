import os
from typing import Dict, List
from dotenv import load_dotenv
from shared.utils import parse_interval

load_dotenv()


class Config:
    # File Server Configuration
    FILE_SERVERS = {}
    
    # Redis Configuration
    REDIS_CONN_STRING = os.getenv("REDIS_CONN_STRING", "redis://localhost:6379/0")
    
    # Update Configuration
    UPDATE_INTERVAL = parse_interval(os.getenv("UPDATE_INTERVAL", "5m"))
    TEMP_CLEAN_INTERVAL = parse_interval(os.getenv("TEMP_CLEAN_INTERVAL", "30m"))
    
    # Server Configuration
    SERVER_PORT = int(os.getenv("SERVER_PORT", 9301))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    API_TOKEN = os.getenv("API_TOKEN", "default_token")
    
    # Paths
    TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tmp")
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    
    @classmethod
    def load_file_servers(cls):
        """Load file server configurations from environment"""
        i = 1
        while True:
            server_key = f"FILE_SERVER_{i}"
            user_key = f"FILE_SERVER_{i}_USER"
            pass_key = f"FILE_SERVER_{i}_PASS"
            
            server_path = os.getenv(server_key)
            if not server_path:
                break
                
            cls.FILE_SERVERS[f"server_{i}"] = {
                "path": server_path,
                "username": os.getenv(user_key, ""),
                "password": os.getenv(pass_key, ""),
                "name": f"Server {i}"
            }
            i += 1
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)


# Load configuration
Config.load_file_servers()
Config.ensure_directories()