import asyncio
import os
import sys
from typing import List, Dict, Optional
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit, 
                           QPushButton, QLabel, QStatusBar, QMessageBox, QProgressBar,
                           QMenu, QHeaderView, QComboBox, QGroupBox, QSplitter,
                           QTextEdit, QFrame, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QCursor
import qtawesome as qta
from ui.styles import (COMPLETE_STYLE, BUTTON_STYLE, SECONDARY_BUTTON_STYLE, 
                      OUTLINE_BUTTON_STYLE, COLORS)
from api_client import api_client
from adb_manager import adb_manager
from config import ClientConfig
from shared.utils import format_file_size


class SearchWorker(QThread):
    """Worker thread for API calls"""
    search_completed = pyqtSignal(list, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, keyword: str, server: str, build_type: str, limit: int, offset: int):
        super().__init__()
        self.keyword = keyword
        self.server = server
        self.build_type = build_type
        self.limit = limit
        self.offset = offset
    
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
            
            self.search_completed.emit(files, total)
            loop.close()
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class DownloadWorker(QThread):
    """Worker thread for file downloads"""
    progress_updated = pyqtSignal(int)
    download_completed = pyqtSignal(bool, str)
    
    def __init__(self, path: str, server: str, local_path: str):
        super().__init__()
        self.path = path
        self.server = server
        self.local_path = local_path
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            def progress_callback(progress):
                self.progress_updated.emit(progress)
            
            success = loop.run_until_complete(
                api_client.download_file(
                    self.path, self.server, self.local_path, progress_callback
                )
            )
            
            self.download_completed.emit(success, self.local_path)
            loop.close()
            
        except Exception as e:
            self.download_completed.emit(False, str(e))


class APKFinderMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_files = []
        self.servers = []
        self.search_worker = None
        self.download_worker = None
        
        self.init_ui()
        self.load_servers()
        self.load_initial_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("APK Finder")
        self.setGeometry(100, 100, ClientConfig.WINDOW_WIDTH, ClientConfig.WINDOW_HEIGHT)
        self.setWindowIcon(qta.icon('mdi.android', color=COLORS["primary"]))
        
        # Apply styles
        self.setStyleSheet(COMPLETE_STYLE)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.create_header(main_layout)
        
        # Server selection and build type tabs
        self.create_controls(main_layout)
        
        # Search section
        self.create_search_section(main_layout)
        
        # Content splitter
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # File list
        self.create_file_list(content_splitter)
        
        # Download panel
        self.create_download_panel(content_splitter)
        
        # Status bar
        self.create_status_bar()
        
        # Set splitter proportions
        content_splitter.setSizes([800, 400])
    
    def create_header(self, layout):
        """Create header section"""
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("APK Finder")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {COLORS["text_primary"]};
                margin: 0;
            }}
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setIcon(qta.icon('mdi.refresh', color=COLORS["white"]))
        self.refresh_btn.setStyleSheet(BUTTON_STYLE)
        self.refresh_btn.clicked.connect(self.refresh_scan)
        header_layout.addWidget(self.refresh_btn)
        
        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setIcon(qta.icon('mdi.cog', color=COLORS["white"]))
        self.settings_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.settings_btn.clicked.connect(self.show_settings)
        header_layout.addWidget(self.settings_btn)
        
        layout.addLayout(header_layout)
    
    def create_controls(self, layout):
        """Create server selection and build type controls"""
        controls_layout = QHBoxLayout()
        
        # Server selection
        server_group = QGroupBox("Server")
        server_layout = QHBoxLayout(server_group)
        
        self.server_combo = QComboBox()
        self.server_combo.addItem("All Servers", "")
        server_layout.addWidget(self.server_combo)
        
        controls_layout.addWidget(server_group)
        
        # Build type tabs
        build_group = QGroupBox("Build Type")
        build_layout = QHBoxLayout(build_group)
        
        self.build_type_tabs = QTabWidget()
        self.build_type_tabs.addTab(QWidget(), "Release")
        self.build_type_tabs.addTab(QWidget(), "Debug")
        self.build_type_tabs.addTab(QWidget(), "Combine")
        self.build_type_tabs.currentChanged.connect(self.on_build_type_changed)
        
        build_layout.addWidget(self.build_type_tabs)
        controls_layout.addWidget(build_group)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
    
    def create_search_section(self, layout):
        """Create search section"""
        search_layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search APK files... (use | to separate multiple keywords)")
        self.search_input.returnPressed.connect(self.search_files)
        search_layout.addWidget(self.search_input)
        
        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setIcon(qta.icon('mdi.magnify', color=COLORS["white"]))
        self.search_btn.setStyleSheet(BUTTON_STYLE)
        self.search_btn.clicked.connect(self.search_files)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
    
    def create_file_list(self, splitter):
        """Create file list table"""
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        # File list header
        list_header = QLabel("File List")
        list_header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {COLORS["text_primary"]};
                margin-bottom: 10px;
            }}
        """)
        list_layout.addWidget(list_header)
        
        # Table widget
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels([
            "File Name", "Size", "Build Type", "Created Time", "Server"
        ])
        
        # Configure table
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        
        list_layout.addWidget(self.file_table)
        
        splitter.addWidget(list_widget)
    
    def create_download_panel(self, splitter):
        """Create download panel"""
        download_widget = QWidget()
        download_layout = QVBoxLayout(download_widget)
        
        # Download header
        download_header = QLabel("Download")
        download_header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {COLORS["text_primary"]};
                margin-bottom: 10px;
            }}
        """)
        download_layout.addWidget(download_header)
        
        # Download info
        self.download_info = QTextEdit()
        self.download_info.setMaximumHeight(150)
        self.download_info.setReadOnly(True)
        self.download_info.setPlaceholderText("Select a file to see download information...")
        download_layout.addWidget(self.download_info)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        download_layout.addWidget(self.progress_bar)
        
        # Download buttons
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download")
        self.download_btn.setIcon(qta.icon('mdi.download', color=COLORS["white"]))
        self.download_btn.setStyleSheet(BUTTON_STYLE)
        self.download_btn.clicked.connect(self.download_selected_file)
        self.download_btn.setEnabled(False)
        button_layout.addWidget(self.download_btn)
        
        self.install_btn = QPushButton("Auto Install")
        self.install_btn.setIcon(qta.icon('mdi.cellphone-android', color=COLORS["white"]))
        self.install_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.install_btn.clicked.connect(self.auto_install_file)
        self.install_btn.setEnabled(False)
        button_layout.addWidget(self.install_btn)
        
        download_layout.addLayout(button_layout)
        
        # Device info
        device_group = QGroupBox("Connected Devices")
        device_layout = QVBoxLayout(device_group)
        
        self.device_list = QTextEdit()
        self.device_list.setMaximumHeight(100)
        self.device_list.setReadOnly(True)
        device_layout.addWidget(self.device_list)
        
        self.refresh_devices_btn = QPushButton("Refresh Devices")
        self.refresh_devices_btn.setIcon(qta.icon('mdi.refresh', color=COLORS["primary"]))
        self.refresh_devices_btn.setStyleSheet(OUTLINE_BUTTON_STYLE)
        self.refresh_devices_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(self.refresh_devices_btn)
        
        download_layout.addWidget(device_group)
        
        download_layout.addStretch()
        
        splitter.addWidget(download_widget)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Connection status
        self.connection_label = QLabel("Checking connection...")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # Check connection periodically
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(30000)  # Check every 30 seconds
        self.check_connection()
    
    def load_servers(self):
        """Load available servers"""
        def load_servers_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                servers = loop.run_until_complete(api_client.get_servers())
                
                self.servers = servers
                self.server_combo.clear()
                self.server_combo.addItem("All Servers", "")
                
                for server in servers:
                    self.server_combo.addItem(server["display_name"], server["name"])
                
                loop.close()
                
            except Exception as e:
                self.show_error(f"Failed to load servers: {e}")
        
        QTimer.singleShot(100, load_servers_async)
    
    def load_initial_data(self):
        """Load initial data (latest files)"""
        self.search_files_internal("", limit=ClientConfig.DEFAULT_RESULTS_PER_PAGE)
    
    def search_files(self):
        """Search for files"""
        keyword = self.search_input.text().strip()
        self.search_files_internal(keyword)
    
    def search_files_internal(self, keyword: str, limit: int = None):
        """Internal search method"""
        if self.search_worker and self.search_worker.isRunning():
            return
        
        server = self.server_combo.currentData() or None
        build_type = self.get_current_build_type()
        limit = limit or ClientConfig.DEFAULT_RESULTS_PER_PAGE
        
        self.search_btn.setEnabled(False)
        self.status_label.setText("Searching...")
        
        self.search_worker = SearchWorker(keyword, server, build_type, limit, 0)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()
    
    def get_current_build_type(self) -> str:
        """Get current build type from tabs"""
        tab_index = self.build_type_tabs.currentIndex()
        if tab_index == 0:
            return "release"
        elif tab_index == 1:
            return "debug"
        else:
            return "combine"
    
    def on_build_type_changed(self):
        """Handle build type tab change"""
        self.search_files_internal("", limit=ClientConfig.DEFAULT_RESULTS_PER_PAGE)
    
    def on_search_completed(self, files: List[Dict], total: int):
        """Handle search completion"""
        self.current_files = files
        self.populate_file_table(files)
        
        self.search_btn.setEnabled(True)
        self.status_label.setText(f"Found {total} files")
    
    def on_search_error(self, error: str):
        """Handle search error"""
        self.search_btn.setEnabled(True)
        self.status_label.setText("Search failed")
        self.show_error(f"Search failed: {error}")
    
    def populate_file_table(self, files: List[Dict]):
        """Populate file table with data"""
        self.file_table.setRowCount(len(files))
        
        for row, file in enumerate(files):
            # File name
            name_item = QTableWidgetItem(file["file_name"])
            name_item.setData(Qt.UserRole, file)
            self.file_table.setItem(row, 0, name_item)
            
            # File size
            size_item = QTableWidgetItem(format_file_size(file["file_size"]))
            self.file_table.setItem(row, 1, size_item)
            
            # Build type
            build_item = QTableWidgetItem(file["build_type"])
            self.file_table.setItem(row, 2, build_item)
            
            # Created time
            created_time = datetime.fromisoformat(file["created_time"].replace('Z', '+00:00'))
            time_item = QTableWidgetItem(created_time.strftime("%Y-%m-%d %H:%M"))
            self.file_table.setItem(row, 3, time_item)
            
            # Server
            server_item = QTableWidgetItem(file.get("server_prefix", "Unknown"))
            self.file_table.setItem(row, 4, server_item)
        
        # Connect selection change
        self.file_table.itemSelectionChanged.connect(self.on_file_selected)
    
    def on_file_selected(self):
        """Handle file selection"""
        current_row = self.file_table.currentRow()
        if current_row >= 0:
            file_data = self.file_table.item(current_row, 0).data(Qt.UserRole)
            self.show_file_info(file_data)
            self.download_btn.setEnabled(True)
            self.update_install_button()
        else:
            self.download_btn.setEnabled(False)
            self.install_btn.setEnabled(False)
    
    def show_file_info(self, file_data: Dict):
        """Show file information in download panel"""
        info_text = f"""
<b>File:</b> {file_data['file_name']}<br>
<b>Size:</b> {format_file_size(file_data['file_size'])}<br>
<b>Build Type:</b> {file_data['build_type']}<br>
<b>Created:</b> {file_data['created_time']}<br>
<b>Server:</b> {file_data['server_prefix']}<br>
<b>Path:</b> {file_data['relative_path']}<br>
<b>Downloads:</b> {file_data.get('download_time', 0)} times
        """
        
        if file_data.get('md5'):
            info_text += f"<br><b>MD5:</b> {file_data['md5']}"
        
        self.download_info.setHtml(info_text)
    
    def show_context_menu(self, position):
        """Show context menu for file table"""
        if self.file_table.itemAt(position) is None:
            return
        
        current_row = self.file_table.currentRow()
        if current_row < 0:
            return
        
        file_data = self.file_table.item(current_row, 0).data(Qt.UserRole)
        
        menu = QMenu(self)
        
        # Copy SMB path
        copy_smb_action = menu.addAction(qta.icon('mdi.content-copy'), "Copy SMB Path")
        copy_smb_action.triggered.connect(lambda: self.copy_smb_path(file_data))
        
        # Copy HTTP path
        copy_http_action = menu.addAction(qta.icon('mdi.link'), "Copy HTTP Path")
        copy_http_action.triggered.connect(lambda: self.copy_http_path(file_data))
        
        menu.addSeparator()
        
        # Download
        download_action = menu.addAction(qta.icon('mdi.download'), "Download")
        download_action.triggered.connect(self.download_selected_file)
        
        # Auto install submenu
        devices = adb_manager.get_connected_devices()
        if devices:
            install_menu = menu.addMenu(qta.icon('mdi.cellphone-android'), "Auto Install")
            
            if len(devices) == 1:
                device = devices[0]
                install_action = install_menu.addAction(f"{device['model']} ({device['serial']})")
                install_action.triggered.connect(lambda: self.install_to_device(file_data, device['serial']))
            else:
                for device in devices:
                    install_action = install_menu.addAction(f"{device['model']} ({device['serial']})")
                    install_action.triggered.connect(lambda checked, d=device: self.install_to_device(file_data, d['serial']))
        
        menu.addSeparator()
        
        # File details
        details_action = menu.addAction(qta.icon('mdi.information'), "File Details")
        details_action.triggered.connect(lambda: self.show_file_details(file_data))
        
        menu.exec_(self.file_table.mapToGlobal(position))
    
    def copy_smb_path(self, file_data: Dict):
        """Copy SMB path to clipboard"""
        smb_path = f"{file_data['server_prefix']}{file_data['relative_path']}"
        QApplication.clipboard().setText(smb_path)
        self.status_label.setText("SMB path copied to clipboard")
    
    def copy_http_path(self, file_data: Dict):
        """Copy HTTP path to clipboard"""
        # Convert SMB path to HTTP path
        server_prefix = file_data['server_prefix']
        relative_path = file_data['relative_path']
        
        # Extract server IP from SMB path
        if server_prefix.startswith('\\\\'):
            parts = server_prefix.split('\\')
            if len(parts) >= 4:
                server_ip = parts[2]
                share_path = '/'.join(parts[3:])
                http_path = f"http://{server_ip}/{share_path}{relative_path.replace('\\', '/')}"
                
                QApplication.clipboard().setText(http_path)
                self.status_label.setText("HTTP path copied to clipboard")
                return
        
        self.show_error("Cannot generate HTTP path from SMB path")
    
    def download_selected_file(self):
        """Download selected file"""
        current_row = self.file_table.currentRow()
        if current_row < 0:
            return
        
        file_data = self.file_table.item(current_row, 0).data(Qt.UserRole)
        
        # Generate local file path
        download_dir = ClientConfig.get_setting("download_path", ClientConfig.DEFAULT_DOWNLOAD_PATH)
        os.makedirs(download_dir, exist_ok=True)
        
        local_path = os.path.join(download_dir, file_data['file_name'])
        
        # Start download
        if self.download_worker and self.download_worker.isRunning():
            self.show_error("Another download is in progress")
            return
        
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Downloading...")
        
        # Find server name from file data
        server_name = self.find_server_name_from_prefix(file_data['server_prefix'])
        
        self.download_worker = DownloadWorker(
            file_data['relative_path'], 
            server_name, 
            local_path
        )
        self.download_worker.progress_updated.connect(self.progress_bar.setValue)
        self.download_worker.download_completed.connect(self.on_download_completed)
        self.download_worker.start()
    
    def find_server_name_from_prefix(self, prefix: str) -> str:
        """Find server name from prefix"""
        for server in self.servers:
            if server["path"] == prefix:
                return server["name"]
        return "server_1"  # fallback
    
    def on_download_completed(self, success: bool, path_or_error: str):
        """Handle download completion"""
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"Downloaded: {os.path.basename(path_or_error)}")
            self.show_info(f"File downloaded successfully:\n{path_or_error}")
        else:
            self.status_label.setText("Download failed")
            self.show_error(f"Download failed: {path_or_error}")
    
    def auto_install_file(self):
        """Auto install selected file"""
        devices = adb_manager.get_connected_devices()
        if not devices:
            self.show_error("No devices connected. Please connect a device and enable USB debugging.")
            return
        
        current_row = self.file_table.currentRow()
        if current_row < 0:
            return
        
        file_data = self.file_table.item(current_row, 0).data(Qt.UserRole)
        
        if len(devices) == 1:
            self.install_to_device(file_data, devices[0]['serial'])
        else:
            # Show device selection menu
            self.show_device_selection(file_data, devices)
    
    def install_to_device(self, file_data: Dict, device_serial: str):
        """Install APK to specific device"""
        # First download the file
        download_dir = ClientConfig.get_setting("download_path", ClientConfig.DEFAULT_DOWNLOAD_PATH)
        local_path = os.path.join(download_dir, file_data['file_name'])
        
        if not os.path.exists(local_path):
            self.show_error("File not downloaded yet. Please download first.")
            return
        
        # Install using ADB
        success, output = adb_manager.install_apk(local_path, device_serial)
        
        if success:
            self.show_info(f"APK installed successfully to device {device_serial}")
            self.status_label.setText("Installation completed")
        else:
            self.show_error(f"Installation failed:\n{output}")
            self.status_label.setText("Installation failed")
    
    def update_install_button(self):
        """Update install button state"""
        devices = adb_manager.get_connected_devices()
        self.install_btn.setEnabled(len(devices) > 0)
    
    def refresh_devices(self):
        """Refresh connected devices"""
        devices = adb_manager.get_connected_devices()
        
        if devices:
            device_text = "\n".join([f"📱 {device['model']} ({device['serial']})" for device in devices])
        else:
            device_text = "No devices connected"
        
        self.device_list.setText(device_text)
        self.update_install_button()
    
    def refresh_scan(self):
        """Refresh server scan"""
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Refreshing...")
        
        def refresh_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                success = loop.run_until_complete(api_client.refresh_scan())
                
                if success:
                    self.status_label.setText("Refresh triggered successfully")
                    QTimer.singleShot(2000, lambda: self.search_files_internal("", limit=ClientConfig.DEFAULT_RESULTS_PER_PAGE))
                else:
                    self.status_label.setText("Refresh failed")
                
                self.refresh_btn.setEnabled(True)
                loop.close()
                
            except Exception as e:
                self.refresh_btn.setEnabled(True)
                self.status_label.setText("Refresh failed")
                self.show_error(f"Refresh failed: {e}")
        
        QTimer.singleShot(100, refresh_async)
    
    def check_connection(self):
        """Check server connection"""
        def check_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                healthy = loop.run_until_complete(api_client.health_check())
                
                if healthy:
                    self.connection_label.setText("🟢 Connected")
                    self.connection_label.setStyleSheet(f"color: {COLORS['success']};")
                else:
                    self.connection_label.setText("🔴 Disconnected")
                    self.connection_label.setStyleSheet(f"color: {COLORS['error']};")
                
                loop.close()
                
            except Exception:
                self.connection_label.setText("🔴 Connection Error")
                self.connection_label.setStyleSheet(f"color: {COLORS['error']};")
        
        QTimer.singleShot(100, check_async)
    
    def show_settings(self):
        """Show settings dialog"""
        from settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec_()
    
    def show_file_details(self, file_data: Dict):
        """Show detailed file information"""
        QMessageBox.information(self, "File Details", 
                              f"File: {file_data['file_name']}\n"
                              f"Size: {format_file_size(file_data['file_size'])}\n"
                              f"Build Type: {file_data['build_type']}\n"
                              f"Created: {file_data['created_time']}\n"
                              f"Server: {file_data['server_prefix']}\n"
                              f"Path: {file_data['relative_path']}\n"
                              f"Downloads: {file_data.get('download_time', 0)}\n"
                              f"MD5: {file_data.get('md5', 'Not calculated')}")
    
    def show_device_selection(self, file_data: Dict, devices: List[Dict]):
        """Show device selection dialog"""
        # This would typically be a custom dialog, simplified here
        device_names = [f"{d['model']} ({d['serial']})" for d in devices]
        from PyQt5.QtWidgets import QInputDialog
        
        device_name, ok = QInputDialog.getItem(
            self, "Select Device", "Choose device for installation:", 
            device_names, 0, False
        )
        
        if ok and device_name:
            device_serial = devices[device_names.index(device_name)]['serial']
            self.install_to_device(file_data, device_serial)
    
    def show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
    
    def show_info(self, message: str):
        """Show info message"""
        QMessageBox.information(self, "Information", message)
    
    def closeEvent(self, event):
        """Handle application close"""
        # Stop any running workers
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.terminate()
        
        event.accept()