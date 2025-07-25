#!/usr/bin/env python3
"""
APK Finder Client
Main entry point for the client application
"""

import sys
import os
import signal
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon, QPainter
import qtawesome as qta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import ClientConfig
from main_window import APKFinderMainWindow


class APKFinderApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application properties
        self.setApplicationName("APK Finder")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("APK Finder")
        
        # Set Windows Application ID for taskbar icon
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("APKFinder.APKFinder.1.0.0")
        except:
            pass  # Ignore errors on non-Windows systems
        
        # Load configuration
        self.load_config()
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "images.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.setWindowIcon(app_icon)
            # Force set as application icon for taskbar
            QApplication.setWindowIcon(app_icon)
        else:
            # Fallback to font icon
            fallback_icon = qta.icon('mdi.android', color='#3B82F6')
            self.setWindowIcon(fallback_icon)
            QApplication.setWindowIcon(fallback_icon)
        
        # Create and show splash screen
        self.splash = self.create_splash_screen()
        self.splash.show()
        
        # Process events to show splash
        self.processEvents()
        
        # Initialize main window
        QTimer.singleShot(2000, self.init_main_window)
    
    def load_config(self):
        """Load application configuration"""
        try:
            config = ClientConfig.load_config()
            
            # Apply font settings
            font_size = config.get("font_size", 14)
            font = QFont("Segoe UI", font_size)
            self.setFont(font)
            
            # Apply theme
            theme = config.get("theme", "Light")
            from ui.styles import update_colors
            update_colors(theme)
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def create_splash_screen(self):
        """Create splash screen"""
        # Try to load custom icon for splash screen
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "images.ico")
        
        if os.path.exists(icon_path):
            # Load and scale the icon
            icon = QPixmap(icon_path)
            if not icon.isNull():
                # Scale icon to reasonable size while maintaining aspect ratio
                icon = icon.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Create larger splash screen with icon embedded
                splash_pix = QPixmap(400, 300)
                splash_pix.fill(Qt.white)
                
                # Draw the icon on the splash screen
                painter = QPainter(splash_pix)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                
                # Calculate position to center the icon
                icon_x = (splash_pix.width() - icon.width()) // 2
                icon_y = (splash_pix.height() - icon.height()) // 2 - 30  # Move up a bit for text
                
                painter.drawPixmap(icon_x, icon_y, icon)
                painter.end()
                
                # Create splash screen
                splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
                
                # Set custom icon for splash screen window (for taskbar)
                splash.setWindowIcon(QIcon(icon_path))
                
                # Show loading message
                splash.showMessage(
                    "Loading APK Finder...\nVersion 1.0.0", 
                    Qt.AlignHCenter | Qt.AlignBottom, 
                    Qt.black
                )
                
                return splash
        
        # Fallback to simple splash screen
        splash_pix = QPixmap(400, 300)
        splash_pix.fill(Qt.white)
        
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        
        # Show loading message
        splash.showMessage(
            "Loading APK Finder...\nVersion 1.0.0", 
            Qt.AlignHCenter | Qt.AlignBottom, 
            Qt.black
        )
        
        return splash
    
    def init_main_window(self):
        """Initialize and show main window"""
        try:
            self.main_window = APKFinderMainWindow()
            
            # Load window settings
            config = ClientConfig.load_config()
            
            if config.get("remember_window_size", True):
                # Restore window geometry if available
                geometry = config.get("window_geometry")
                if geometry:
                    self.main_window.restoreGeometry(bytes.fromhex(geometry))
            
            if config.get("start_maximized", False):
                self.main_window.showMaximized()
            else:
                self.main_window.show()
            
            # Close splash screen
            self.splash.finish(self.main_window)
            
            # Check initial connection
            QTimer.singleShot(1000, self.main_window.check_connection)
            
        except Exception as e:
            self.splash.close()
            QMessageBox.critical(
                None, 
                "Startup Error", 
                f"Failed to initialize APK Finder:\n\n{str(e)}\n\nPlease check your configuration and try again."
            )
            self.quit()
    
    def save_window_state(self):
        """Save window state before closing"""
        try:
            if hasattr(self, 'main_window'):
                config = ClientConfig.load_config()
                
                # Save window geometry
                geometry = self.main_window.saveGeometry().toHex().data().decode()
                config["window_geometry"] = geometry
                
                # Save window state
                state = self.main_window.saveState().toHex().data().decode()
                config["window_state"] = state
                
                ClientConfig.save_config(config)
                
        except Exception as e:
            print(f"Error saving window state: {e}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.save_window_state()
        super().closeEvent(event)


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down...")
    QApplication.quit()


def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import PyQt5
    except ImportError:
        missing_deps.append("PyQt5")
    
    try:
        import qtawesome
    except ImportError:
        missing_deps.append("qtawesome")
    
    try:
        import httpx
    except ImportError:
        missing_deps.append("httpx")
    
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies with:")
        print(f"  pip install {' '.join(missing_deps)}")
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
    
    # Enable high DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = APKFinderApp(sys.argv)
    
    # Set up exception handling
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}"
        print(error_msg)
        
        # Show error dialog if GUI is available
        if QApplication.instance():
            QMessageBox.critical(None, "Unexpected Error", error_msg)
    
    sys.excepthook = handle_exception
    
    # Run application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()