import asyncio
import os
import sys
from typing import List, Dict, Optional
from datetime import datetime
import threading
from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.widget import Widget
from kivy.uix.splitter import Splitter
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.app import App

# Import shared modules
from api_client import api_client
from adb_manager import adb_manager
from config import ClientConfig
from shared.utils import format_file_size


class SearchWorker(threading.Thread):
    """Worker thread for API calls"""
    
    def __init__(self, callback, error_callback, keyword: str, server: str, build_type: str, limit: int, offset: int):
        super().__init__()
        self.callback = callback
        self.error_callback = error_callback
        self.keyword = keyword
        self.server = server
        self.build_type = build_type
        self.limit = limit
        self.offset = offset
        self.daemon = True
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            files, total = loop.run_until_complete(
                api_client.search_apk_files(
                    self.keyword, self.server, self.build_type, 
                    self.limit, self.offset
                )
            )
            
            # Schedule callback on main thread
            Clock.schedule_once(lambda dt: self.callback(files, total), 0)
            loop.close()
            
        except Exception as e:
            # Schedule error callback on main thread
            Clock.schedule_once(lambda dt: self.error_callback(str(e)), 0)


class DownloadWorker(threading.Thread):
    """Worker thread for file downloads"""
    
    def __init__(self, progress_callback, completion_callback, path: str, server: str, local_path: str):
        super().__init__()
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.path = path
        self.server = server
        self.local_path = local_path
        self.daemon = True
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            def progress_callback(progress):
                Clock.schedule_once(lambda dt: self.progress_callback(progress), 0)
            
            success = loop.run_until_complete(
                api_client.download_file(
                    self.path, self.server, self.local_path, progress_callback
                )
            )
            
            Clock.schedule_once(lambda dt: self.completion_callback(success, self.local_path), 0)
            loop.close()
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.completion_callback(False, str(e)), 0)


class FileListWidget(ScrollView):
    """Custom widget for file list with table-like appearance"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.files = []
        self.selected_row = -1
        self.row_widgets = []
        self.selection_callback = None
        
        # Create container
        self.container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.container.bind(minimum_height=self.container.setter('height'))
        
        # Create header
        self.create_header()
        
        self.add_widget(self.container)
    
    def create_header(self):
        """Create table header"""
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        
        # Column headers
        headers = ["File Name", "Size", "Build Type", "Created Time", "Server"]
        for header_text in headers:
            label = Label(
                text=header_text,
                size_hint_x=0.3 if header_text == "File Name" else 0.175,
                text_size=(None, None),
                halign='left',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))
            header.add_widget(label)
        
        self.container.add_widget(header)
    
    def populate_files(self, files: List[Dict]):
        """Populate file list with data"""
        self.files = files
        
        # Clear existing rows
        for widget in self.row_widgets:
            self.container.remove_widget(widget)
        self.row_widgets.clear()
        
        # Add new rows
        for i, file in enumerate(files):
            row = self.create_file_row(file, i)
            self.container.add_widget(row)
            self.row_widgets.append(row)
    
    def create_file_row(self, file: Dict, row_index: int):
        """Create a file row widget"""
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40)
        )
        
        # File name
        name_label = Label(
            text=file["file_name"],
            size_hint_x=0.3,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        name_label.bind(size=name_label.setter('text_size'))
        row.add_widget(name_label)
        
        # File size
        size_label = Label(
            text=format_file_size(file["file_size"]),
            size_hint_x=0.175,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        size_label.bind(size=size_label.setter('text_size'))
        row.add_widget(size_label)
        
        # Build type
        build_label = Label(
            text=file["build_type"],
            size_hint_x=0.175,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        build_label.bind(size=build_label.setter('text_size'))
        row.add_widget(build_label)
        
        # Created time
        try:
            created_time = datetime.fromisoformat(file["created_time"].replace('Z', '+00:00'))
            time_str = created_time.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            time_str = "Unknown"
        
        time_label = Label(
            text=time_str,
            size_hint_x=0.175,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        time_label.bind(size=time_label.setter('text_size'))
        row.add_widget(time_label)
        
        # Server
        server_label = Label(
            text=file.get("server_prefix", "Unknown"),
            size_hint_x=0.175,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        server_label.bind(size=server_label.setter('text_size'))
        row.add_widget(server_label)
        
        # Add selection behavior
        def on_row_press(instance):
            self.select_row(row_index)
        
        # Create invisible button for selection
        select_btn = Button(
            text='',
            background_color=(0, 0, 0, 0),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        select_btn.bind(on_press=on_row_press)
        
        # Add button to row
        row.add_widget(select_btn)
        
        return row
    
    def select_row(self, row_index: int):
        """Select a row"""
        self.selected_row = row_index
        
        # Update visual selection (you can customize this)
        for i, row in enumerate(self.row_widgets):
            if i == row_index:
                row.canvas.before.clear()
                with row.canvas.before:
                    from kivy.graphics import Color, Rectangle
                    Color(0.2, 0.4, 0.8, 0.3)  # Light blue selection
                    Rectangle(pos=row.pos, size=row.size)
            else:
                row.canvas.before.clear()
        
        # Trigger callback
        if self.selection_callback:
            self.selection_callback(row_index)
    
    def get_selected_file(self):
        """Get currently selected file"""
        if 0 <= self.selected_row < len(self.files):
            return self.files[self.selected_row]
        return None


class APKFinderMainScreen(Screen):
    """Main screen for APK Finder"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize data
        self.current_files = []
        self.servers = []
        self.search_worker = None
        self.download_worker = None
        self.selected_server = None
        self.selected_build_type = "release"
        self.cached_devices = []
        self.recent_downloads = []
        
        # Build UI
        self.build_ui()
        
        # Load initial data
        Clock.schedule_once(self.load_initial_data, 0.5)
    
    def build_ui(self):
        """Build the user interface"""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # Header
        self.create_header(main_layout)
        
        # Controls
        self.create_controls(main_layout)
        
        # Search section
        self.create_search_section(main_layout)
        
        # Content area (split between file list and download panel)
        content_splitter = Splitter(
            orientation='vertical',
            sizable_from='right',
            size_hint=(1, 0.7)
        )
        
        # File list
        self.create_file_list(content_splitter)
        
        # Download panel
        self.create_download_panel(content_splitter)
        
        main_layout.add_widget(content_splitter)
        
        # Status bar
        self.create_status_bar(main_layout)
        
        self.add_widget(main_layout)
    
    def create_header(self, parent):
        """Create header section"""
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        # Title
        title_label = Label(
            text="APK Finder",
            font_size=dp(24),
            size_hint_x=0.3,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        header_layout.add_widget(title_label)
        
        # Spacer
        header_layout.add_widget(Widget(size_hint_x=0.4))
        
        # Control buttons
        self.refresh_btn = Button(
            text="Refresh",
            size_hint_x=0.1,
            size_hint_y=None,
            height=dp(40)
        )
        self.refresh_btn.bind(on_press=self.refresh_scan)
        header_layout.add_widget(self.refresh_btn)
        
        self.settings_btn = Button(
            text="Settings",
            size_hint_x=0.1,
            size_hint_y=None,
            height=dp(40)
        )
        self.settings_btn.bind(on_press=self.show_settings)
        header_layout.add_widget(self.settings_btn)
        
        parent.add_widget(header_layout)
    
    def create_controls(self, parent):
        """Create server and build type controls"""
        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(20))
        
        # Server selection
        server_layout = BoxLayout(orientation='vertical', size_hint_x=0.5)
        server_layout.add_widget(Label(text="Server:", size_hint_y=None, height=dp(20)))
        
        self.server_spinner = Spinner(
            text="All Servers",
            values=["All Servers"],
            size_hint_y=None,
            height=dp(40)
        )
        self.server_spinner.bind(text=self.on_server_selected)
        server_layout.add_widget(self.server_spinner)
        
        controls_layout.add_widget(server_layout)
        
        # Build type selection
        build_layout = BoxLayout(orientation='vertical', size_hint_x=0.5)
        build_layout.add_widget(Label(text="Build Type:", size_hint_y=None, height=dp(20)))
        
        build_buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        
        self.release_btn = Button(text="Release", state='down')
        self.release_btn.bind(on_press=lambda x: self.on_build_type_selected("release"))
        build_buttons.add_widget(self.release_btn)
        
        self.debug_btn = Button(text="Debug")
        self.debug_btn.bind(on_press=lambda x: self.on_build_type_selected("debug"))
        build_buttons.add_widget(self.debug_btn)
        
        self.combine_btn = Button(text="Combine")
        self.combine_btn.bind(on_press=lambda x: self.on_build_type_selected("combine"))
        build_buttons.add_widget(self.combine_btn)
        
        build_layout.add_widget(build_buttons)
        controls_layout.add_widget(build_layout)
        
        parent.add_widget(controls_layout)
    
    def create_search_section(self, parent):
        """Create search section"""
        search_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        
        # Search input
        self.search_input = TextInput(
            hint_text="Search APK files... (use | to separate multiple keywords)",
            multiline=False,
            size_hint_x=0.8
        )
        self.search_input.bind(on_text_validate=self.search_files)
        search_layout.add_widget(self.search_input)
        
        # Search button
        self.search_btn = Button(
            text="Search",
            size_hint_x=0.2
        )
        self.search_btn.bind(on_press=self.search_files)
        search_layout.add_widget(self.search_btn)
        
        parent.add_widget(search_layout)
    
    def create_file_list(self, parent):
        """Create file list section"""
        file_section = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        # File list header
        file_header = Label(
            text="File List",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16)
        )
        file_section.add_widget(file_header)
        
        # File list widget
        self.file_list = FileListWidget()
        self.file_list.selection_callback = self.on_file_selected
        file_section.add_widget(self.file_list)
        
        parent.add_widget(file_section)
    
    def create_download_panel(self, parent):
        """Create download panel"""
        download_section = BoxLayout(orientation='vertical', size_hint_x=0.3)
        
        # Download header
        download_header = Label(
            text="Download",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16)
        )
        download_section.add_widget(download_header)
        
        # Recent downloads
        self.recent_downloads_text = TextInput(
            text="No recent downloads...",
            readonly=True,
            size_hint_y=0.4
        )
        download_section.add_widget(self.recent_downloads_text)
        
        # Progress bar
        self.progress_bar = ProgressBar(
            size_hint_y=None,
            height=dp(20)
        )
        self.progress_bar.opacity = 0
        download_section.add_widget(self.progress_bar)
        
        # Action buttons
        button_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), spacing=dp(10))
        
        self.download_btn = Button(
            text="Download",
            size_hint_y=None,
            height=dp(40),
            disabled=True
        )
        self.download_btn.bind(on_press=self.download_selected_file)
        button_layout.add_widget(self.download_btn)
        
        self.install_btn = Button(
            text="Auto Install",
            size_hint_y=None,
            height=dp(40),
            disabled=True
        )
        self.install_btn.bind(on_press=self.auto_install_file)
        button_layout.add_widget(self.install_btn)
        
        self.clear_recent_btn = Button(
            text="Clear Recent",
            size_hint_y=None,
            height=dp(40)
        )
        self.clear_recent_btn.bind(on_press=self.clear_recent_downloads)
        button_layout.add_widget(self.clear_recent_btn)
        
        download_section.add_widget(button_layout)
        
        # Device info
        device_section = BoxLayout(orientation='vertical', size_hint_y=0.3)
        
        device_header = Label(
            text="Connected Devices",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14)
        )
        device_section.add_widget(device_header)
        
        self.device_list_text = TextInput(
            text="No devices connected",
            readonly=True,
            size_hint_y=0.7
        )
        device_section.add_widget(self.device_list_text)
        
        self.refresh_devices_btn = Button(
            text="Refresh Devices",
            size_hint_y=None,
            height=dp(40)
        )
        self.refresh_devices_btn.bind(on_press=self.refresh_devices)
        device_section.add_widget(self.refresh_devices_btn)
        
        download_section.add_widget(device_section)
        
        parent.add_widget(download_section)
    
    def create_status_bar(self, parent):
        """Create status bar"""
        status_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        
        self.status_label = Label(
            text="Ready",
            size_hint_x=0.7,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_layout.add_widget(self.status_label)
        
        self.connection_label = Label(
            text="Checking connection...",
            size_hint_x=0.3,
            text_size=(None, None),
            halign='right',
            valign='middle'
        )
        self.connection_label.bind(size=self.connection_label.setter('text_size'))
        status_layout.add_widget(self.connection_label)
        
        parent.add_widget(status_layout)
    
    def on_app_start(self, dt):
        """Called when app starts"""
        self.load_servers()
        self.load_initial_data()
        self.refresh_devices()
        self.check_connection()
        
        # Schedule periodic connection check
        Clock.schedule_interval(self.check_connection, 30)
    
    def load_servers(self, dt=None):
        """Load available servers"""
        def load_servers_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                servers = loop.run_until_complete(api_client.get_servers())
                
                # Schedule UI update on main thread
                Clock.schedule_once(lambda dt: self.update_servers_ui(servers), 0)
                loop.close()
                
            except Exception as e:
                Logger.error(f"APKFinder: Failed to load servers: {e}")
                Clock.schedule_once(lambda dt: self.show_error(f"Failed to load servers: {e}"), 0)
        
        threading.Thread(target=load_servers_async, daemon=True).start()
    
    def update_servers_ui(self, servers):
        """Update servers UI on main thread"""
        self.servers = servers
        
        # Update server spinner
        server_values = ["All Servers"]
        server_values.extend([server["display_name"] for server in servers])
        self.server_spinner.values = server_values
    
    def load_initial_data(self, dt=None):
        """Load initial data (latest files)"""
        self.search_files_internal("", limit=ClientConfig.DEFAULT_RESULTS_PER_PAGE)
    
    def search_files(self, instance=None):
        """Search for files"""
        keyword = self.search_input.text.strip()
        self.search_files_internal(keyword)
    
    def search_files_internal(self, keyword: str, limit: int = None):
        """Internal search method"""
        if self.search_worker and self.search_worker.is_alive():
            return
        
        server = self.selected_server
        build_type = self.selected_build_type
        limit = limit or ClientConfig.DEFAULT_RESULTS_PER_PAGE
        
        self.search_btn.disabled = True
        self.status_label.text = "Searching..."
        
        self.search_worker = SearchWorker(
            self.on_search_completed,
            self.on_search_error,
            keyword, server, build_type, limit, 0
        )
        self.search_worker.start()
    
    def on_search_completed(self, files: List[Dict], total: int):
        """Handle search completion"""
        self.current_files = files
        self.file_list.populate_files(files)
        
        self.search_btn.disabled = False
        self.status_label.text = f"Found {total} files"
    
    def on_search_error(self, error: str):
        """Handle search error"""
        self.search_btn.disabled = False
        self.status_label.text = "Search failed"
        self.show_error(f"Search failed: {error}")
    
    def on_server_selected(self, instance, server_name):
        """Handle server selection"""
        if server_name == "All Servers":
            self.selected_server = None
        else:
            # Find server by display name
            for server in self.servers:
                if server["display_name"] == server_name:
                    self.selected_server = server["name"]
                    break
        
        # Trigger search with new server selection
        self.search_files_internal("", limit=ClientConfig.DEFAULT_RESULTS_PER_PAGE)
    
    def on_build_type_selected(self, build_type):
        """Handle build type selection"""
        self.selected_build_type = build_type
        
        # Update button states
        self.release_btn.state = 'down' if build_type == 'release' else 'normal'
        self.debug_btn.state = 'down' if build_type == 'debug' else 'normal'
        self.combine_btn.state = 'down' if build_type == 'combine' else 'normal'
        
        # Trigger search with new build type
        self.search_files_internal("", limit=ClientConfig.DEFAULT_RESULTS_PER_PAGE)
    
    def on_file_selected(self, row_index):
        """Handle file selection"""
        if row_index >= 0:
            self.download_btn.disabled = False
            self.update_install_button()
        else:
            self.download_btn.disabled = True
            self.install_btn.disabled = True
    
    def download_selected_file(self, instance):
        """Download selected file"""
        file_data = self.file_list.get_selected_file()
        if not file_data:
            return
        
        # Generate local file path
        download_dir = ClientConfig.get_setting("download_path", ClientConfig.DEFAULT_DOWNLOAD_PATH)
        os.makedirs(download_dir, exist_ok=True)
        
        local_path = os.path.join(download_dir, file_data['file_name'])
        
        # Start download
        if self.download_worker and self.download_worker.is_alive():
            self.show_error("Another download is in progress")
            return
        
        self.download_btn.disabled = True
        self.progress_bar.opacity = 1
        self.progress_bar.value = 0
        self.status_label.text = "Downloading..."
        
        # Find server name from file data
        server_name = self.find_server_name_from_prefix(file_data['server_prefix'])
        
        self.download_worker = DownloadWorker(
            self.on_download_progress,
            self.on_download_completed,
            file_data['relative_path'],
            server_name,
            local_path
        )
        self.download_worker.start()
    
    def on_download_progress(self, progress):
        """Handle download progress"""
        self.progress_bar.value = progress
    
    def on_download_completed(self, success: bool, path_or_error: str):
        """Handle download completion"""
        self.download_btn.disabled = False
        self.progress_bar.opacity = 0
        
        if success:
            file_name = os.path.basename(path_or_error)
            self.status_label.text = f"Downloaded: {file_name}"
            self.show_info(f"File downloaded successfully:\n{path_or_error}")
            self.add_recent_download(file_name, path_or_error)
        else:
            self.status_label.text = "Download failed"
            self.show_error(f"Download failed: {path_or_error}")
    
    def auto_install_file(self, instance):
        """Auto install selected file"""
        if not self.cached_devices:
            self.show_error("No devices connected. Please connect a device and refresh devices list.")
            return
        
        file_data = self.file_list.get_selected_file()
        if not file_data:
            return
        
        if len(self.cached_devices) == 1:
            self.install_to_device(file_data, self.cached_devices[0]['serial'])
        else:
            # Show device selection (simplified for now)
            self.show_info("Multiple devices detected. Using first device.")
            self.install_to_device(file_data, self.cached_devices[0]['serial'])
    
    def install_to_device(self, file_data: Dict, device_serial: str):
        """Install APK to specific device"""
        # First check if file is downloaded
        download_dir = ClientConfig.get_setting("download_path", ClientConfig.DEFAULT_DOWNLOAD_PATH)
        local_path = os.path.join(download_dir, file_data['file_name'])
        
        if not os.path.exists(local_path):
            self.show_error("File not downloaded yet. Please download first.")
            return
        
        # Install using ADB
        success, output = adb_manager.install_apk(local_path, device_serial)
        
        if success:
            self.show_info(f"APK installed successfully to device {device_serial}")
            self.status_label.text = "Installation completed"
        else:
            self.show_error(f"Installation failed:\n{output}")
            self.status_label.text = "Installation failed"
    
    def update_install_button(self):
        """Update install button state"""
        self.install_btn.disabled = len(self.cached_devices) == 0
    
    def refresh_devices(self, instance=None):
        """Refresh connected devices"""
        self.cached_devices = adb_manager.get_connected_devices()
        
        if self.cached_devices:
            device_text = "\n".join([f"📱 {device['model']} ({device['serial']})" for device in self.cached_devices])
        else:
            device_text = "No devices connected"
        
        self.device_list_text.text = device_text
        self.update_install_button()
    
    def add_recent_download(self, file_name: str, file_path: str):
        """Add a file to recent downloads"""
        download_info = {
            "name": file_name,
            "path": file_path,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Remove if already exists
        self.recent_downloads = [d for d in self.recent_downloads if d["name"] != file_name]
        
        # Add to beginning
        self.recent_downloads.insert(0, download_info)
        
        # Keep only last 10 downloads
        self.recent_downloads = self.recent_downloads[:10]
        
        # Update display
        self.update_recent_downloads_display()
    
    def update_recent_downloads_display(self):
        """Update recent downloads display"""
        if not self.recent_downloads:
            self.recent_downloads_text.text = "No recent downloads..."
            return
        
        download_text = ""
        for download in self.recent_downloads:
            download_text += f"📁 {download['name']}\n"
            download_text += f"   {download['time']}\n\n"
        
        self.recent_downloads_text.text = download_text.strip()
    
    def clear_recent_downloads(self, instance):
        """Clear recent downloads list"""
        self.recent_downloads.clear()
        self.update_recent_downloads_display()
    
    def refresh_scan(self, instance):
        """Refresh server scan"""
        self.refresh_btn.disabled = True
        self.status_label.text = "Refreshing..."
        
        def refresh_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                success = loop.run_until_complete(api_client.refresh_scan())
                
                if success:
                    Clock.schedule_once(lambda dt: self.on_refresh_success(), 0)
                else:
                    Clock.schedule_once(lambda dt: self.on_refresh_failed(), 0)
                
                loop.close()
                
            except Exception as e:
                Clock.schedule_once(lambda dt: self.on_refresh_error(str(e)), 0)
        
        threading.Thread(target=refresh_async, daemon=True).start()
    
    def on_refresh_success(self):
        """Handle successful refresh"""
        self.status_label.text = "Refresh triggered successfully"
        self.refresh_btn.disabled = False
        Clock.schedule_once(lambda dt: self.search_files_internal("", limit=ClientConfig.DEFAULT_RESULTS_PER_PAGE), 2)
    
    def on_refresh_failed(self):
        """Handle failed refresh"""
        self.status_label.text = "Refresh failed"
        self.refresh_btn.disabled = False
    
    def on_refresh_error(self, error):
        """Handle refresh error"""
        self.refresh_btn.disabled = False
        self.status_label.text = "Refresh failed"
        self.show_error(f"Refresh failed: {error}")
    
    def check_connection(self, dt=None):
        """Check server connection"""
        def check_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                healthy = loop.run_until_complete(api_client.health_check())
                
                if healthy:
                    Clock.schedule_once(lambda dt: self.on_connection_ok(), 0)
                else:
                    Clock.schedule_once(lambda dt: self.on_connection_failed(), 0)
                
                loop.close()
                
            except Exception:
                Clock.schedule_once(lambda dt: self.on_connection_error(), 0)
        
        threading.Thread(target=check_async, daemon=True).start()
    
    def on_connection_ok(self):
        """Handle successful connection"""
        self.connection_label.text = "🟢 Connected"
    
    def on_connection_failed(self):
        """Handle failed connection"""
        self.connection_label.text = "🔴 Disconnected"
    
    def on_connection_error(self):
        """Handle connection error"""
        self.connection_label.text = "🔴 Connection Error"
    
    def show_settings(self, instance):
        """Show settings dialog"""
        from settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        dialog.open()
    
    def find_server_name_from_prefix(self, prefix: str) -> str:
        """Find server name from prefix"""
        for server in self.servers:
            if server["path"] == prefix:
                return server["name"]
        return "server_1"  # fallback
    
    def show_error(self, message: str):
        """Show error message"""
        popup = Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def show_info(self, message: str):
        """Show info message"""
        popup = Popup(
            title="Information",
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def cleanup(self):
        """Clean up resources"""
        # Stop any running workers
        if self.search_worker and self.search_worker.is_alive():
            # Can't terminate threads in Python, but they're daemon threads
            pass
        if self.download_worker and self.download_worker.is_alive():
            # Can't terminate threads in Python, but they're daemon threads
            pass