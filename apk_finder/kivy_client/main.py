#!/usr/bin/env python3
"""
APK Finder Kivy Client
Main entry point for the Kivy-based client application
"""

import sys
import os
import signal
import asyncio
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.config import Config
from kivy.clock import Clock
from kivy.logger import Logger

# Configure Kivy before importing other modules
Config.set('kivy', 'desktop', 1)
Config.set('graphics', 'resizable', 1)
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '800')

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import ClientConfig
from main_window import APKFinderMainScreen


class APKFinderApp(App):
    """Main Kivy Application class"""
    
    def __init__(self):
        super().__init__()
        self.title = "APK Finder"
        self.icon = self.get_icon_path()
        
        # Load configuration
        self.load_config()
        
        # Initialize screen manager
        self.screen_manager = None
        self.main_screen = None
        
    def get_icon_path(self):
        """Get application icon path"""
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        if os.path.exists(icon_path):
            return icon_path
        return None
    
    def load_config(self):
        """Load application configuration"""
        try:
            config = ClientConfig.load_config()
            Logger.info(f"APKFinder: Configuration loaded successfully")
            
            # Apply theme settings
            theme = config.get("theme", "Light")
            Logger.info(f"APKFinder: Theme set to {theme}")
            
        except Exception as e:
            Logger.error(f"APKFinder: Error loading configuration: {e}")
    
    def build(self):
        """Build the main application interface"""
        Logger.info("APKFinder: Building main application interface")
        
        # Create screen manager
        self.screen_manager = ScreenManager()
        
        # Create main screen
        self.main_screen = APKFinderMainScreen(name='main')
        self.screen_manager.add_widget(self.main_screen)
        
        # Set initial screen
        self.screen_manager.current = 'main'
        
        return self.screen_manager
    
    def on_start(self):
        """Called when the application starts"""
        Logger.info("APKFinder: Application started")
        
        # Perform initial setup
        if self.main_screen:
            Clock.schedule_once(self.main_screen.on_app_start, 0.1)
    
    def on_stop(self):
        """Called when the application stops"""
        Logger.info("APKFinder: Application stopping")
        
        # Clean up resources
        if self.main_screen:
            self.main_screen.cleanup()
        
        # Stop any running workers
        self.stop_workers()
    
    def stop_workers(self):
        """Stop all background workers"""
        try:
            # Stop async loops if any
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
        except Exception as e:
            Logger.error(f"APKFinder: Error stopping workers: {e}")
    
    def on_pause(self):
        """Called when the application is paused (Android)"""
        Logger.info("APKFinder: Application paused")
        return True
    
    def on_resume(self):
        """Called when the application resumes (Android)"""
        Logger.info("APKFinder: Application resumed")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    Logger.info(f"APKFinder: Received signal {signum}, shutting down...")
    if hasattr(App.get_running_app(), 'stop'):
        App.get_running_app().stop()


def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import kivy
        Logger.info(f"APKFinder: Kivy version {kivy.__version__} found")
    except ImportError:
        missing_deps.append("kivy")
    
    try:
        import httpx
    except ImportError:
        missing_deps.append("httpx")
    
    if missing_deps:
        Logger.error("APKFinder: Missing required dependencies:")
        for dep in missing_deps:
            Logger.error(f"  - {dep}")
        Logger.error("Please install missing dependencies with:")
        Logger.error(f"  pip install {' '.join(missing_deps)}")
        return False
    
    return True


def main():
    """Main function"""
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run application
    try:
        app = APKFinderApp()
        app.run()
    except KeyboardInterrupt:
        Logger.info("APKFinder: Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        Logger.error(f"APKFinder: Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()