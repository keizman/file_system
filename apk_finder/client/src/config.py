import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class ClientConfig:
    # Server Configuration
    SERVER_URL = os.getenv("SERVER_URL", "http://localhost:9301")
    API_TOKEN = os.getenv("API_TOKEN", "default_token")
    
    # Client Configuration
    DEFAULT_DOWNLOAD_PATH = os.getenv("DEFAULT_DOWNLOAD_PATH", os.path.expanduser("~/Downloads/APK"))
    MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "50"))
    DEFAULT_RESULTS_PER_PAGE = int(os.getenv("DEFAULT_RESULTS_PER_PAGE", "10"))
    
    # UI Configuration
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "800"))
    THEME = os.getenv("THEME", "light")
    
    # Cache Configuration
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".apk_finder")
    CONFIG_FILE = os.path.join(CACHE_DIR, "config.json")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
        os.makedirs(cls.DEFAULT_DOWNLOAD_PATH, exist_ok=True)
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}
    
    @classmethod
    def save_config(cls, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    @classmethod
    def get_setting(cls, key: str, default=None):
        """Get a setting value"""
        config = cls.load_config()
        return config.get(key, default)
    
    @classmethod
    def set_setting(cls, key: str, value):
        """Set a setting value"""
        config = cls.load_config()
        config[key] = value
        cls.save_config(config)


# Initialize configuration
ClientConfig.ensure_directories()