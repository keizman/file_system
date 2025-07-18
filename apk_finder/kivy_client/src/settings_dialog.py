import asyncio
import os
import threading
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.logger import Logger

from config import ClientConfig


class SettingsDialog(Popup):
    """Settings dialog for APK Finder"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.title = "Settings"
        self.size_hint = (0.9, 0.9)
        self.auto_dismiss = False
        
        # Build UI
        self.build_ui()
        
        # Load current settings
        self.load_settings()
    
    def build_ui(self):
        """Build the settings interface"""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Create tabbed panel
        self.tab_panel = TabbedPanel(
            do_default_tab=False,
            tab_width=dp(120)
        )
        
        # Create tabs
        self.create_general_tab()
        self.create_server_tab()
        self.create_download_tab()
        self.create_ui_tab()
        self.create_advanced_tab()
        
        main_layout.add_widget(self.tab_panel)
        
        # Button layout
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        # Cancel button
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=self.cancel_settings)
        button_layout.add_widget(cancel_btn)
        
        # Apply button
        apply_btn = Button(text="Apply")
        apply_btn.bind(on_press=self.apply_settings)
        button_layout.add_widget(apply_btn)
        
        # OK button
        ok_btn = Button(text="OK")
        ok_btn.bind(on_press=self.accept_settings)
        button_layout.add_widget(ok_btn)
        
        main_layout.add_widget(button_layout)
        
        self.content = main_layout
    
    def create_general_tab(self):
        """Create general settings tab"""
        tab = TabbedPanelItem(text="General")
        
        # Scrollable content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Application settings
        app_section = self.create_section("Application Settings")
        
        # Auto check updates
        self.auto_check_updates = CheckBox(active=True)
        app_section.add_widget(self.create_setting_row("Automatically check for updates", self.auto_check_updates))
        
        # Startup scan
        self.startup_scan = CheckBox(active=False)
        app_section.add_widget(self.create_setting_row("Perform scan on startup", self.startup_scan))
        
        # Minimize to tray
        self.minimize_to_tray = CheckBox(active=False)
        app_section.add_widget(self.create_setting_row("Minimize to system tray", self.minimize_to_tray))
        
        content.add_widget(app_section)
        
        # Search settings
        search_section = self.create_section("Search Settings")
        
        # Max results
        self.max_results = Slider(min=10, max=1000, value=50, step=10)
        self.max_results_label = Label(text="50")
        self.max_results.bind(value=self.on_max_results_change)
        search_section.add_widget(self.create_setting_row("Max Results", self.max_results, self.max_results_label))
        
        # Results per page
        self.results_per_page = Slider(min=5, max=100, value=10, step=5)
        self.results_per_page_label = Label(text="10")
        self.results_per_page.bind(value=self.on_results_per_page_change)
        search_section.add_widget(self.create_setting_row("Results per Page", self.results_per_page, self.results_per_page_label))
        
        # Search history
        self.search_history = CheckBox(active=True)
        search_section.add_widget(self.create_setting_row("Save search history", self.search_history))
        
        content.add_widget(search_section)
        
        scroll.add_widget(content)
        tab.content = scroll
        self.tab_panel.add_widget(tab)
    
    def create_server_tab(self):
        """Create server settings tab"""
        tab = TabbedPanelItem(text="Server")
        
        # Scrollable content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Server connection
        server_section = self.create_section("Server Connection")
        
        # Server URL
        self.server_url = TextInput(
            text="http://localhost:9301",
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        server_section.add_widget(self.create_setting_row("Server URL", self.server_url))
        
        # API Token
        self.api_token = TextInput(
            text="",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        server_section.add_widget(self.create_setting_row("API Token", self.api_token))
        
        # Test connection button
        self.test_connection_btn = Button(
            text="Test Connection",
            size_hint_y=None,
            height=dp(40)
        )
        self.test_connection_btn.bind(on_press=self.test_connection)
        server_section.add_widget(self.test_connection_btn)
        
        content.add_widget(server_section)
        
        # Connection settings
        conn_section = self.create_section("Connection Settings")
        
        # Connection timeout
        self.connection_timeout = Slider(min=5, max=300, value=30, step=5)
        self.connection_timeout_label = Label(text="30 seconds")
        self.connection_timeout.bind(value=self.on_connection_timeout_change)
        conn_section.add_widget(self.create_setting_row("Connection Timeout", self.connection_timeout, self.connection_timeout_label))
        
        # Retry attempts
        self.retry_attempts = Slider(min=1, max=10, value=3, step=1)
        self.retry_attempts_label = Label(text="3")
        self.retry_attempts.bind(value=self.on_retry_attempts_change)
        conn_section.add_widget(self.create_setting_row("Retry Attempts", self.retry_attempts, self.retry_attempts_label))
        
        content.add_widget(conn_section)
        
        scroll.add_widget(content)
        tab.content = scroll
        self.tab_panel.add_widget(tab)
    
    def create_download_tab(self):
        """Create download settings tab"""
        tab = TabbedPanelItem(text="Download")
        
        # Scrollable content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Download paths
        path_section = self.create_section("Download Paths")
        
        # Default download path
        download_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.download_path = TextInput(
            text="",
            multiline=False,
            size_hint_x=0.8
        )
        download_layout.add_widget(self.download_path)
        
        browse_btn = Button(text="Browse", size_hint_x=0.2)
        browse_btn.bind(on_press=self.browse_download_path)
        download_layout.add_widget(browse_btn)
        
        path_section.add_widget(self.create_setting_row("Default Download Path", download_layout))
        
        # Temporary files path
        temp_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.temp_path = TextInput(
            text="",
            multiline=False,
            size_hint_x=0.8
        )
        temp_layout.add_widget(self.temp_path)
        
        browse_temp_btn = Button(text="Browse", size_hint_x=0.2)
        browse_temp_btn.bind(on_press=self.browse_temp_path)
        temp_layout.add_widget(browse_temp_btn)
        
        path_section.add_widget(self.create_setting_row("Temporary Files Path", temp_layout))
        
        content.add_widget(path_section)
        
        # Download behavior
        behavior_section = self.create_section("Download Behavior")
        
        # Auto verify MD5
        self.auto_verify_md5 = CheckBox(active=False)
        behavior_section.add_widget(self.create_setting_row("Automatically verify MD5 checksums", self.auto_verify_md5))
        
        # Overwrite existing
        self.overwrite_existing = CheckBox(active=False)
        behavior_section.add_widget(self.create_setting_row("Overwrite existing files", self.overwrite_existing))
        
        # Open download folder
        self.open_download_folder = CheckBox(active=False)
        behavior_section.add_widget(self.create_setting_row("Open download folder after completion", self.open_download_folder))
        
        # Max concurrent downloads
        self.max_concurrent_downloads = Slider(min=1, max=10, value=3, step=1)
        self.max_concurrent_downloads_label = Label(text="3")
        self.max_concurrent_downloads.bind(value=self.on_max_concurrent_downloads_change)
        behavior_section.add_widget(self.create_setting_row("Max Concurrent Downloads", self.max_concurrent_downloads, self.max_concurrent_downloads_label))
        
        content.add_widget(behavior_section)
        
        scroll.add_widget(content)
        tab.content = scroll
        self.tab_panel.add_widget(tab)
    
    def create_ui_tab(self):
        """Create UI settings tab"""
        tab = TabbedPanelItem(text="UI")
        
        # Scrollable content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Appearance
        appearance_section = self.create_section("Appearance")
        
        # Theme
        self.theme_combo = Spinner(
            text="Light",
            values=["Light", "Dark", "Auto"],
            size_hint_y=None,
            height=dp(40)
        )
        self.theme_combo.bind(text=self.on_theme_changed)
        appearance_section.add_widget(self.create_setting_row("Theme", self.theme_combo))
        
        # Font size
        self.font_size = Slider(min=8, max=24, value=14, step=1)
        self.font_size_label = Label(text="14 pt")
        self.font_size.bind(value=self.on_font_size_change)
        appearance_section.add_widget(self.create_setting_row("Font Size", self.font_size, self.font_size_label))
        
        # Show file icons
        self.show_file_icons = CheckBox(active=True)
        appearance_section.add_widget(self.create_setting_row("Show file type icons", self.show_file_icons))
        
        content.add_widget(appearance_section)
        
        # Window settings
        window_section = self.create_section("Window Settings")
        
        # Remember window size
        self.remember_window_size = CheckBox(active=True)
        window_section.add_widget(self.create_setting_row("Remember window size and position", self.remember_window_size))
        
        # Start maximized
        self.start_maximized = CheckBox(active=False)
        window_section.add_widget(self.create_setting_row("Start maximized", self.start_maximized))
        
        content.add_widget(window_section)
        
        # Table settings
        table_section = self.create_section("Table Settings")
        
        # Show grid lines
        self.show_grid_lines = CheckBox(active=True)
        table_section.add_widget(self.create_setting_row("Show grid lines", self.show_grid_lines))
        
        # Alternate row colors
        self.alternate_row_colors = CheckBox(active=True)
        table_section.add_widget(self.create_setting_row("Alternate row colors", self.alternate_row_colors))
        
        # Auto resize columns
        self.auto_resize_columns = CheckBox(active=True)
        table_section.add_widget(self.create_setting_row("Auto-resize columns", self.auto_resize_columns))
        
        content.add_widget(table_section)
        
        scroll.add_widget(content)
        tab.content = scroll
        self.tab_panel.add_widget(tab)
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = TabbedPanelItem(text="Advanced")
        
        # Scrollable content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # ADB settings
        adb_section = self.create_section("ADB Settings")
        
        # ADB path
        self.adb_path = TextInput(
            text="adb",
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        adb_section.add_widget(self.create_setting_row("ADB Path", self.adb_path))
        
        # ADB timeout
        self.adb_timeout = Slider(min=10, max=300, value=60, step=10)
        self.adb_timeout_label = Label(text="60 seconds")
        self.adb_timeout.bind(value=self.on_adb_timeout_change)
        adb_section.add_widget(self.create_setting_row("ADB Timeout", self.adb_timeout, self.adb_timeout_label))
        
        # Install flags
        self.install_flags = TextInput(
            text="-r -d -t",
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        adb_section.add_widget(self.create_setting_row("Install Flags", self.install_flags))
        
        content.add_widget(adb_section)
        
        # Cache settings
        cache_section = self.create_section("Cache Settings")
        
        # Cache search results
        self.cache_search_results = CheckBox(active=True)
        cache_section.add_widget(self.create_setting_row("Cache search results", self.cache_search_results))
        
        # Cache duration
        self.cache_duration = Slider(min=1, max=24, value=6, step=1)
        self.cache_duration_label = Label(text="6 hours")
        self.cache_duration.bind(value=self.on_cache_duration_change)
        cache_section.add_widget(self.create_setting_row("Cache Duration", self.cache_duration, self.cache_duration_label))
        
        # Clear cache button
        self.clear_cache_btn = Button(
            text="Clear Cache",
            size_hint_y=None,
            height=dp(40)
        )
        self.clear_cache_btn.bind(on_press=self.clear_cache)
        cache_section.add_widget(self.clear_cache_btn)
        
        content.add_widget(cache_section)
        
        # Logging
        logging_section = self.create_section("Logging")
        
        # Log level
        self.log_level = Spinner(
            text="INFO",
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            size_hint_y=None,
            height=dp(40)
        )
        logging_section.add_widget(self.create_setting_row("Log Level", self.log_level))
        
        # Enable file logging
        self.enable_file_logging = CheckBox(active=True)
        logging_section.add_widget(self.create_setting_row("Enable file logging", self.enable_file_logging))
        
        content.add_widget(logging_section)
        
        scroll.add_widget(content)
        tab.content = scroll
        self.tab_panel.add_widget(tab)
    
    def create_section(self, title):
        """Create a section with title"""
        section = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
        section.bind(minimum_height=section.setter('height'))
        
        # Section title
        title_label = Label(
            text=title,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30),
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        section.add_widget(title_label)
        
        return section
    
    def create_setting_row(self, label_text, widget, extra_widget=None):
        """Create a setting row with label and widget"""
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        # Label
        label = Label(
            text=label_text,
            size_hint_x=0.4,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        label.bind(size=label.setter('text_size'))
        row.add_widget(label)
        
        # Widget
        widget.size_hint_x = 0.4 if extra_widget else 0.6
        row.add_widget(widget)
        
        # Extra widget (like value label)
        if extra_widget:
            extra_widget.size_hint_x = 0.2
            row.add_widget(extra_widget)
        
        return row
    
    def load_settings(self):
        """Load settings from configuration"""
        config = ClientConfig.load_config()
        
        # General settings
        self.auto_check_updates.active = config.get("auto_check_updates", True)
        self.startup_scan.active = config.get("startup_scan", False)
        self.minimize_to_tray.active = config.get("minimize_to_tray", False)
        self.max_results.value = config.get("max_results", ClientConfig.MAX_SEARCH_RESULTS)
        self.results_per_page.value = config.get("results_per_page", ClientConfig.DEFAULT_RESULTS_PER_PAGE)
        self.search_history.active = config.get("search_history", True)
        
        # Server settings
        self.server_url.text = config.get("server_url", ClientConfig.SERVER_URL)
        self.api_token.text = config.get("api_token", ClientConfig.API_TOKEN)
        self.connection_timeout.value = config.get("connection_timeout", 30)
        self.retry_attempts.value = config.get("retry_attempts", 3)
        
        # Download settings
        self.download_path.text = config.get("download_path", ClientConfig.DEFAULT_DOWNLOAD_PATH)
        self.temp_path.text = config.get("temp_path", ClientConfig.CACHE_DIR)
        self.auto_verify_md5.active = config.get("auto_verify_md5", False)
        self.overwrite_existing.active = config.get("overwrite_existing", False)
        self.open_download_folder.active = config.get("open_download_folder", False)
        self.max_concurrent_downloads.value = config.get("max_concurrent_downloads", 3)
        
        # UI settings
        theme = config.get("theme", "Light")
        if theme in ["Light", "Dark", "Auto"]:
            self.theme_combo.text = theme
        self.font_size.value = config.get("font_size", 14)
        self.show_file_icons.active = config.get("show_file_icons", True)
        self.remember_window_size.active = config.get("remember_window_size", True)
        self.start_maximized.active = config.get("start_maximized", False)
        self.show_grid_lines.active = config.get("show_grid_lines", True)
        self.alternate_row_colors.active = config.get("alternate_row_colors", True)
        self.auto_resize_columns.active = config.get("auto_resize_columns", True)
        
        # Advanced settings
        self.adb_path.text = config.get("adb_path", "adb")
        self.adb_timeout.value = config.get("adb_timeout", 60)
        self.install_flags.text = config.get("install_flags", "-r -d -t")
        self.cache_search_results.active = config.get("cache_search_results", True)
        self.cache_duration.value = config.get("cache_duration", 6)
        log_level = config.get("log_level", "INFO")
        if log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            self.log_level.text = log_level
        self.enable_file_logging.active = config.get("enable_file_logging", True)
    
    def save_settings(self):
        """Save settings to configuration"""
        config = {
            # General
            "auto_check_updates": self.auto_check_updates.active,
            "startup_scan": self.startup_scan.active,
            "minimize_to_tray": self.minimize_to_tray.active,
            "max_results": int(self.max_results.value),
            "results_per_page": int(self.results_per_page.value),
            "search_history": self.search_history.active,
            
            # Server
            "server_url": self.server_url.text.strip(),
            "api_token": self.api_token.text.strip(),
            "connection_timeout": int(self.connection_timeout.value),
            "retry_attempts": int(self.retry_attempts.value),
            
            # Download
            "download_path": self.download_path.text.strip(),
            "temp_path": self.temp_path.text.strip(),
            "auto_verify_md5": self.auto_verify_md5.active,
            "overwrite_existing": self.overwrite_existing.active,
            "open_download_folder": self.open_download_folder.active,
            "max_concurrent_downloads": int(self.max_concurrent_downloads.value),
            
            # UI
            "theme": self.theme_combo.text,
            "font_size": int(self.font_size.value),
            "show_file_icons": self.show_file_icons.active,
            "remember_window_size": self.remember_window_size.active,
            "start_maximized": self.start_maximized.active,
            "show_grid_lines": self.show_grid_lines.active,
            "alternate_row_colors": self.alternate_row_colors.active,
            "auto_resize_columns": self.auto_resize_columns.active,
            
            # Advanced
            "adb_path": self.adb_path.text.strip(),
            "adb_timeout": int(self.adb_timeout.value),
            "install_flags": self.install_flags.text.strip(),
            "cache_search_results": self.cache_search_results.active,
            "cache_duration": int(self.cache_duration.value),
            "log_level": self.log_level.text,
            "enable_file_logging": self.enable_file_logging.active,
        }
        
        ClientConfig.save_config(config)
    
    def browse_download_path(self, instance):
        """Browse for download path"""
        # Simple popup for path selection (you can enhance this)
        popup = Popup(
            title="Select Download Directory",
            content=Label(text="Path selection not implemented yet"),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def browse_temp_path(self, instance):
        """Browse for temporary path"""
        # Simple popup for path selection (you can enhance this)
        popup = Popup(
            title="Select Temporary Directory",
            content=Label(text="Path selection not implemented yet"),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def test_connection(self, instance):
        """Test server connection"""
        from api_client import APIClient
        
        # Create temporary API client with current settings
        temp_client = APIClient()
        temp_client.base_url = self.server_url.text.strip()
        temp_client.headers["Authorization"] = f"Bearer {self.api_token.text.strip()}"
        
        self.test_connection_btn.disabled = True
        self.test_connection_btn.text = "Testing..."
        
        def test_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                healthy = loop.run_until_complete(temp_client.health_check())
                
                if healthy:
                    Clock.schedule_once(lambda dt: self.on_connection_test_success(), 0)
                else:
                    Clock.schedule_once(lambda dt: self.on_connection_test_failed(), 0)
                
                loop.close()
                
            except Exception as e:
                Clock.schedule_once(lambda dt: self.on_connection_test_error(str(e)), 0)
        
        threading.Thread(target=test_async, daemon=True).start()
        
        # Reset button after 3 seconds
        Clock.schedule_once(self.reset_test_button, 3)
    
    def on_connection_test_success(self):
        """Handle successful connection test"""
        popup = Popup(
            title="Connection Test",
            content=Label(text="✅ Connection successful!"),
            size_hint=(0.6, 0.3)
        )
        popup.open()
    
    def on_connection_test_failed(self):
        """Handle failed connection test"""
        popup = Popup(
            title="Connection Test",
            content=Label(text="❌ Connection failed!"),
            size_hint=(0.6, 0.3)
        )
        popup.open()
    
    def on_connection_test_error(self, error):
        """Handle connection test error"""
        popup = Popup(
            title="Connection Test",
            content=Label(text=f"❌ Connection error: {error}"),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def reset_test_button(self, dt):
        """Reset test connection button"""
        self.test_connection_btn.disabled = False
        self.test_connection_btn.text = "Test Connection"
    
    def clear_cache(self, instance):
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
            
            popup = Popup(
                title="Clear Cache",
                content=Label(text="Cache cleared successfully!"),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            
        except Exception as e:
            popup = Popup(
                title="Clear Cache",
                content=Label(text=f"Failed to clear cache: {e}"),
                size_hint=(0.8, 0.4)
            )
            popup.open()
    
    def apply_settings(self, instance):
        """Apply settings without closing dialog"""
        self.save_settings()
        popup = Popup(
            title="Settings",
            content=Label(text="Settings saved successfully!"),
            size_hint=(0.6, 0.3)
        )
        popup.open()
    
    def accept_settings(self, instance):
        """Accept and save settings"""
        self.save_settings()
        self.dismiss()
    
    def cancel_settings(self, instance):
        """Cancel changes"""
        self.dismiss()
    
    # Event handlers for sliders
    def on_max_results_change(self, instance, value):
        self.max_results_label.text = str(int(value))
    
    def on_results_per_page_change(self, instance, value):
        self.results_per_page_label.text = str(int(value))
    
    def on_connection_timeout_change(self, instance, value):
        self.connection_timeout_label.text = f"{int(value)} seconds"
    
    def on_retry_attempts_change(self, instance, value):
        self.retry_attempts_label.text = str(int(value))
    
    def on_max_concurrent_downloads_change(self, instance, value):
        self.max_concurrent_downloads_label.text = str(int(value))
    
    def on_font_size_change(self, instance, value):
        self.font_size_label.text = f"{int(value)} pt"
    
    def on_adb_timeout_change(self, instance, value):
        self.adb_timeout_label.text = f"{int(value)} seconds"
    
    def on_cache_duration_change(self, instance, value):
        self.cache_duration_label.text = f"{int(value)} hours"
    
    def on_theme_changed(self, instance, theme):
        """Handle theme change"""
        # Save theme immediately
        ClientConfig.set_setting("theme", theme)
        Logger.info(f"APKFinder: Theme changed to {theme}")