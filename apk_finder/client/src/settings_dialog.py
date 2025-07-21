from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QWidget, QLabel, QLineEdit, QPushButton, QFileDialog,
                           QGroupBox, QCheckBox, QSpinBox, QComboBox, QTextEdit,
                           QFormLayout, QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import qtawesome as qta
from ui.styles import get_complete_style, COLORS, get_theme_colors, update_colors, update_style_constants
from config import ClientConfig


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 500)
        # Apply theme
        self.apply_theme()
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_server_tab()
        self.create_download_tab()
        self.create_ui_tab()
        self.create_advanced_tab()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        
        layout.addWidget(button_box)
    
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Application settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)
        
        self.auto_check_updates = QCheckBox("Automatically check for updates")
        app_layout.addRow("Updates:", self.auto_check_updates)
        
        self.startup_scan = QCheckBox("Perform scan on startup")
        app_layout.addRow("Startup:", self.startup_scan)
        
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        app_layout.addRow("Minimize:", self.minimize_to_tray)
        
        layout.addWidget(app_group)
        
        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)
        
        self.max_results = QSpinBox()
        self.max_results.setRange(10, 1000)
        self.max_results.setValue(50)
        search_layout.addRow("Max Results:", self.max_results)
        
        self.results_per_page = QSpinBox()
        self.results_per_page.setRange(5, 100)
        self.results_per_page.setValue(10)
        search_layout.addRow("Results per Page:", self.results_per_page)
        
        self.search_history = QCheckBox("Save search history")
        search_layout.addRow("History:", self.search_history)
        
        layout.addWidget(search_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "General")
    
    def create_server_tab(self):
        """Create server settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Server connection
        server_group = QGroupBox("Server Connection")
        server_layout = QFormLayout(server_group)
        
        self.server_url = QLineEdit()
        self.server_url.setPlaceholderText("http://localhost:9301")
        
        server_layout.addRow("Server URL:", self.server_url)
        
        self.api_token = QLineEdit()
        self.api_token.setEchoMode(QLineEdit.Password)
        self.api_token.setPlaceholderText("Enter API token")
        server_layout.addRow("API Token:", self.api_token)
        
        # Test connection button
        test_layout = QHBoxLayout()
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.setIcon(qta.icon('mdi.network', color=COLORS["white"]))
        self.test_connection_btn.setObjectName("primaryButton")
        self.test_connection_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_connection_btn)
        test_layout.addStretch()
        
        server_layout.addRow("", test_layout)
        
        layout.addWidget(server_group)
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout(conn_group)
        
        self.connection_timeout = QSpinBox()
        self.connection_timeout.setRange(5, 300)
        self.connection_timeout.setValue(30)
        self.connection_timeout.setSuffix(" seconds")
        conn_layout.addRow("Connection Timeout:", self.connection_timeout)
        
        self.retry_attempts = QSpinBox()
        self.retry_attempts.setRange(1, 10)
        self.retry_attempts.setValue(3)
        conn_layout.addRow("Retry Attempts:", self.retry_attempts)
        
        layout.addWidget(conn_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Server")
    
    def create_download_tab(self):
        """Create download settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Download paths
        path_group = QGroupBox("Download Paths")
        path_layout = QFormLayout(path_group)
        
        # Default download path
        download_layout = QHBoxLayout()
        self.download_path = QLineEdit()
        download_layout.addWidget(self.download_path)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("secondaryButton")  # Set button style
        browse_btn.clicked.connect(self.browse_download_path)
        download_layout.addWidget(browse_btn)
        
        path_layout.addRow("Default Download Path:", download_layout)
        
        # Temporary files path
        temp_layout = QHBoxLayout()
        self.temp_path = QLineEdit()
        temp_layout.addWidget(self.temp_path)
        
        browse_temp_btn = QPushButton("Browse...")
        browse_temp_btn.setObjectName("secondaryButton")  # Set button style
        browse_temp_btn.clicked.connect(self.browse_temp_path)
        temp_layout.addWidget(browse_temp_btn)
        
        path_layout.addRow("Temporary Files Path:", temp_layout)
        
        layout.addWidget(path_group)
        
        # Download behavior
        behavior_group = QGroupBox("Download Behavior")
        behavior_layout = QFormLayout(behavior_group)
        
        self.auto_verify_md5 = QCheckBox("Automatically verify MD5 checksums")
        behavior_layout.addRow("Verification:", self.auto_verify_md5)
        
        self.overwrite_existing = QCheckBox("Overwrite existing files")
        behavior_layout.addRow("Overwrite:", self.overwrite_existing)
        
        self.open_download_folder = QCheckBox("Open download folder after completion")
        behavior_layout.addRow("Open Folder:", self.open_download_folder)
        
        self.max_concurrent_downloads = QSpinBox()
        self.max_concurrent_downloads.setRange(1, 10)
        self.max_concurrent_downloads.setValue(3)
        behavior_layout.addRow("Max Concurrent Downloads:", self.max_concurrent_downloads)
        
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Download")
    
    def create_ui_tab(self):
        """Create UI settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(14)
        self.font_size.setSuffix(" pt")
        appearance_layout.addRow("Font Size:", self.font_size)
        
        self.show_file_icons = QCheckBox("Show file type icons")
        appearance_layout.addRow("Icons:", self.show_file_icons)
        
        layout.addWidget(appearance_group)
        
        # Window settings
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout(window_group)
        
        self.remember_window_size = QCheckBox("Remember window size and position")
        window_layout.addRow("Memory:", self.remember_window_size)
        
        self.start_maximized = QCheckBox("Start maximized")
        window_layout.addRow("Startup:", self.start_maximized)
        
        layout.addWidget(window_group)
        
        # Table settings
        table_group = QGroupBox("Table Settings")
        table_layout = QFormLayout(table_group)
        
        self.show_grid_lines = QCheckBox("Show grid lines")
        table_layout.addRow("Grid:", self.show_grid_lines)
        
        self.alternate_row_colors = QCheckBox("Alternate row colors")
        table_layout.addRow("Rows:", self.alternate_row_colors)
        
        self.auto_resize_columns = QCheckBox("Auto-resize columns")
        table_layout.addRow("Columns:", self.auto_resize_columns)
        
        layout.addWidget(table_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "UI")
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # ADB settings
        adb_group = QGroupBox("ADB Settings")
        adb_layout = QFormLayout(adb_group)
        
        self.adb_path = QLineEdit()
        self.adb_path.setPlaceholderText("adb (if in PATH) or full path to adb executable")
        adb_layout.addRow("ADB Path:", self.adb_path)
        
        self.adb_timeout = QSpinBox()
        self.adb_timeout.setRange(10, 300)
        self.adb_timeout.setValue(60)
        self.adb_timeout.setSuffix(" seconds")
        adb_layout.addRow("ADB Timeout:", self.adb_timeout)
        
        self.install_flags = QLineEdit()
        self.install_flags.setPlaceholderText("-r -d -t")
        self.install_flags.setText("-r -d -t")
        adb_layout.addRow("Install Flags:", self.install_flags)
        
        layout.addWidget(adb_group)
        
        # Cache settings
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QFormLayout(cache_group)
        
        self.cache_search_results = QCheckBox("Cache search results")
        cache_layout.addRow("Search Cache:", self.cache_search_results)
        
        self.cache_duration = QSpinBox()
        self.cache_duration.setRange(1, 24)
        self.cache_duration.setValue(6)
        self.cache_duration.setSuffix(" hours")
        cache_layout.addRow("Cache Duration:", self.cache_duration)
        
        # Clear cache button
        clear_cache_layout = QHBoxLayout()
        self.clear_cache_btn = QPushButton("Clear Cache")
        self.clear_cache_btn.setIcon(qta.icon('mdi.delete', color=COLORS["white"]))
        self.clear_cache_btn.setObjectName("primaryButton")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        clear_cache_layout.addWidget(self.clear_cache_btn)
        clear_cache_layout.addStretch()
        
        cache_layout.addRow("", clear_cache_layout)
        
        layout.addWidget(cache_group)
        
        # Logging
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level)
        
        self.enable_file_logging = QCheckBox("Enable file logging")
        logging_layout.addRow("File Logging:", self.enable_file_logging)
        
        layout.addWidget(logging_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced")
    
    def load_settings(self):
        """Load settings from configuration"""
        config = ClientConfig.load_config()
        
        # General settings
        self.auto_check_updates.setChecked(config.get("auto_check_updates", True))
        self.startup_scan.setChecked(config.get("startup_scan", False))
        self.minimize_to_tray.setChecked(config.get("minimize_to_tray", False))
        self.max_results.setValue(config.get("max_results", ClientConfig.MAX_SEARCH_RESULTS))
        self.results_per_page.setValue(config.get("results_per_page", ClientConfig.DEFAULT_RESULTS_PER_PAGE))
        self.search_history.setChecked(config.get("search_history", True))
        
        # Server settings
        self.server_url.setText(config.get("server_url", ClientConfig.SERVER_URL))
        self.api_token.setText(config.get("api_token", ClientConfig.API_TOKEN))
        self.connection_timeout.setValue(config.get("connection_timeout", 30))
        self.retry_attempts.setValue(config.get("retry_attempts", 3))
        
        # Download settings
        self.download_path.setText(config.get("download_path", ClientConfig.DEFAULT_DOWNLOAD_PATH))
        self.temp_path.setText(config.get("temp_path", ClientConfig.CACHE_DIR))
        self.auto_verify_md5.setChecked(config.get("auto_verify_md5", False))
        self.overwrite_existing.setChecked(config.get("overwrite_existing", False))
        self.open_download_folder.setChecked(config.get("open_download_folder", False))
        self.max_concurrent_downloads.setValue(config.get("max_concurrent_downloads", 3))
        
        # UI settings
        theme = config.get("theme", "Light")
        if theme in ["Light", "Dark", "Auto"]:
            self.theme_combo.setCurrentText(theme)
        self.font_size.setValue(config.get("font_size", 14))
        self.show_file_icons.setChecked(config.get("show_file_icons", True))
        self.remember_window_size.setChecked(config.get("remember_window_size", True))
        self.start_maximized.setChecked(config.get("start_maximized", False))
        self.show_grid_lines.setChecked(config.get("show_grid_lines", True))
        self.alternate_row_colors.setChecked(config.get("alternate_row_colors", True))
        self.auto_resize_columns.setChecked(config.get("auto_resize_columns", True))
        
        # Advanced settings
        self.adb_path.setText(config.get("adb_path", "adb"))
        self.adb_timeout.setValue(config.get("adb_timeout", 60))
        self.install_flags.setText(config.get("install_flags", "-r -d -t"))
        self.cache_search_results.setChecked(config.get("cache_search_results", True))
        self.cache_duration.setValue(config.get("cache_duration", 6))
        log_level = config.get("log_level", "INFO")
        if log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            self.log_level.setCurrentText(log_level)
        self.enable_file_logging.setChecked(config.get("enable_file_logging", True))
    
    def save_settings(self):
        """Save settings to configuration"""
        config = {
            # General
            "auto_check_updates": self.auto_check_updates.isChecked(),
            "startup_scan": self.startup_scan.isChecked(),
            "minimize_to_tray": self.minimize_to_tray.isChecked(),
            "max_results": self.max_results.value(),
            "results_per_page": self.results_per_page.value(),
            "search_history": self.search_history.isChecked(),
            
            # Server
            "server_url": self.server_url.text().strip(),
            "api_token": self.api_token.text().strip(),
            "connection_timeout": self.connection_timeout.value(),
            "retry_attempts": self.retry_attempts.value(),
            
            # Download
            "download_path": self.download_path.text().strip(),
            "temp_path": self.temp_path.text().strip(),
            "auto_verify_md5": self.auto_verify_md5.isChecked(),
            "overwrite_existing": self.overwrite_existing.isChecked(),
            "open_download_folder": self.open_download_folder.isChecked(),
            "max_concurrent_downloads": self.max_concurrent_downloads.value(),
            
            # UI
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_size.value(),
            "show_file_icons": self.show_file_icons.isChecked(),
            "remember_window_size": self.remember_window_size.isChecked(),
            "start_maximized": self.start_maximized.isChecked(),
            "show_grid_lines": self.show_grid_lines.isChecked(),
            "alternate_row_colors": self.alternate_row_colors.isChecked(),
            "auto_resize_columns": self.auto_resize_columns.isChecked(),
            
            # Advanced
            "adb_path": self.adb_path.text().strip(),
            "adb_timeout": self.adb_timeout.value(),
            "install_flags": self.install_flags.text().strip(),
            "cache_search_results": self.cache_search_results.isChecked(),
            "cache_duration": self.cache_duration.value(),
            "log_level": self.log_level.currentText(),
            "enable_file_logging": self.enable_file_logging.isChecked(),
        }
        
        ClientConfig.save_config(config)
    
    def browse_download_path(self):
        """Browse for download path"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", self.download_path.text()
        )
        if path:
            self.download_path.setText(path)
    
    def browse_temp_path(self):
        """Browse for temporary path"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory", self.temp_path.text()
        )
        if path:
            self.temp_path.setText(path)
    
    def test_connection(self):
        """Test server connection"""
        import asyncio
        from api_client import APIClient
        
        # Create temporary API client with current settings
        temp_client = APIClient()
        temp_client.base_url = self.server_url.text().strip()
        temp_client.headers["Authorization"] = f"Bearer {self.api_token.text().strip()}"
        
        def test_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                healthy = loop.run_until_complete(temp_client.health_check())
                
                if healthy:
                    QMessageBox.information(self, "Connection Test", "✅ Connection successful!")
                else:
                    QMessageBox.warning(self, "Connection Test", "❌ Connection failed!")
                
                loop.close()
                
            except Exception as e:
                QMessageBox.critical(self, "Connection Test", f"❌ Connection error: {e}")
        
        self.test_connection_btn.setEnabled(False)
        self.test_connection_btn.setText("Testing...")
        
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, test_async)
        
        def reset_button():
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("Test Connection")
        
        QTimer.singleShot(3000, reset_button)
    
    def clear_cache(self):
        """Clear application cache"""
        import shutil
        try:
            cache_dir = ClientConfig.CACHE_DIR
            # Remove cache files but keep config
            for item in os.listdir(cache_dir):
                if item != "config.json":
                    item_path = os.path.join(cache_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
            
            QMessageBox.information(self, "Clear Cache", "Cache cleared successfully!")
            
        except Exception as e:
            QMessageBox.warning(self, "Clear Cache", f"Failed to clear cache: {e}")
    
    def apply_settings(self):
        """Apply settings without closing dialog"""
        self.save_settings()
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
    
    def accept_settings(self):
        """Accept and save settings"""
        self.save_settings()
        self.accept()
    
    def apply_theme(self, theme: str = None):
        """Apply theme to the settings dialog"""
        if theme is None:
            theme = ClientConfig.get_setting("theme", "Light")
        
        # Apply stylesheet
        self.setStyleSheet(get_complete_style(theme))
        
        # Update icon colors based on theme if buttons exist
        colors = get_theme_colors(theme)
        if hasattr(self, 'test_connection_btn'):
            self.test_connection_btn.setIcon(qta.icon('mdi.network', color=colors["white"]))
        if hasattr(self, 'clear_cache_btn'):
            self.clear_cache_btn.setIcon(qta.icon('mdi.delete', color=colors["white"]))
    
    def on_theme_changed(self, theme: str):
        """Handle theme change in real-time"""
        # Save the theme setting immediately
        ClientConfig.set_setting("theme", theme)
        
        # Update global colors and styles
        update_colors(theme)
        update_style_constants(theme)
        
        # Apply theme to dialog
        self.apply_theme(theme)
        
        # Update parent window theme as well
        if self.parent():
            self.parent().apply_theme(theme)
    
    def reject(self):
        """Reject changes"""
        super().reject()