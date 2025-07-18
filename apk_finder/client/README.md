# APK Finder Client

The client application for APK Finder built with PyQt5, providing a modern interface for searching, downloading, and managing APK files.

## Features

- 🎨 **Modern UI**: Beautiful interface with custom styling
- 🔍 **Advanced Search**: Multi-keyword search with filters
- 📱 **ADB Integration**: Direct APK installation to Android devices
- ⬇️ **Smart Downloads**: Progress tracking and MD5 verification
- ⚙️ **Rich Settings**: Comprehensive configuration management
- 📋 **Context Menus**: Quick access to file operations
- 🔗 **Real-time Status**: Server connection monitoring

## Installation

### Requirements

- Python 3.8+
- PyQt5
- Android SDK (for ADB functionality)

### Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure Settings** (optional):
Create `.env` file:
```env
SERVER_URL=http://your-server:9301
API_TOKEN=your_token
DEFAULT_DOWNLOAD_PATH=/path/to/downloads
```

3. **Run Application**:
```bash
python main.py
```

## User Interface

### Main Window Layout

```
┌─────────────────────────────────────────┐
│  APK Finder              [Refresh] [⚙️] │
├─────────────────────────────────────────┤
│ Server: [All Servers ▼] │ Build Type:   │
│                         │ Release Debug │
├─────────────────────────────────────────┤
│ 🔍 Search APK files...           [🔍]   │
├─────────────────────────┬───────────────┤
│ File List               │ Download      │
│ ┌─────────────────────┐ │ ┌───────────┐ │
│ │📦 myapp_v1.2.3.apk │ │ │File Info  │ │
│ │  50MB | 2025-01-17  │ │ │           │ │
│ │📦 myapp_v1.2.2.apk │ │ │[Download] │ │
│ │  48MB | 2025-01-16  │ │ │[Install]  │ │
│ └─────────────────────┘ │ │           │ │
│                         │ │Connected  │ │
│                         │ │Devices:   │ │
│                         │ │📱 Pixel 6 │ │
└─────────────────────────┴───────────────┘
│ Status: 15 files found │ 🟢 Connected │
└─────────────────────────────────────────┘
```

### Build Type Tabs

- **Release**: Show only release builds
- **Debug**: Show only debug builds  
- **Combine**: Show all build types

### File List Table

Columns:
- **File Name**: APK filename with icon
- **Size**: Human-readable file size
- **Build Type**: Release/Debug/Unknown
- **Created Time**: File creation timestamp
- **Server**: Source server information

## Features

### Search Functionality

**Simple Search**:
```
myapp
```

**Multi-keyword Search** (AND logic):
```
myapp|release
debug|v1.2.3
```

**Search Filters**:
- Server selection (All or specific server)
- Build type filtering (Release/Debug/Combine)
- Results pagination

### Context Menu Options

Right-click on any file for:

- **Copy SMB Path**: `\\server\share\path\file.apk`
- **Copy HTTP Path**: `http://server/path/file.apk`
- **Download**: Save file locally
- **Auto Install**: Install to connected Android device(s)
- **File Details**: Show comprehensive file information

### Download Management

**Features**:
- Progress bar with percentage
- MD5 verification (optional)
- Configurable download location
- Automatic directory creation
- Error handling and retry

**Download Info Panel**:
- File metadata display
- Progress tracking
- Status updates

### ADB Integration

**Device Management**:
- Automatic device detection
- Multi-device support
- Device model and serial display
- Connection status monitoring

**Installation Process**:
1. Connect Android device via USB
2. Enable USB debugging
3. Click "Refresh Devices"
4. Right-click APK → Auto Install → Select device
5. APK installs automatically with status feedback

**Installation Flags**:
- `-r`: Replace existing app
- `-d`: Allow version downgrade  
- `-t`: Allow test packages

### Settings Management

Access via Settings button (⚙️) or menu.

#### General Settings
- Auto-check for updates
- Startup scan behavior
- System tray integration
- Search result limits
- Search history

#### Server Settings
- Server URL configuration
- API token management
- Connection timeout
- Retry attempts
- Connection testing

#### Download Settings
- Default download path
- Temporary files location
- MD5 verification toggle
- Overwrite behavior
- Concurrent download limits

#### UI Settings
- Theme selection (Light/Dark/Auto)
- Font size adjustment
- File icons toggle
- Window size memory
- Table appearance

#### Advanced Settings
- ADB path configuration
- Installation flags
- Cache management
- Logging configuration

## Usage Examples

### Basic File Search

1. **Start Application**: Launch `python main.py`
2. **Search Files**: Enter keywords in search box
3. **Filter Results**: Select server and build type
4. **Browse Files**: Click through file list
5. **View Details**: Select file to see information

### Download APK

1. **Find File**: Search and select desired APK
2. **Check Info**: Review file details in download panel
3. **Download**: Click "Download" button
4. **Monitor Progress**: Watch progress bar
5. **Completion**: File saved to configured location

### Install to Device

1. **Connect Device**: USB cable + USB debugging enabled
2. **Refresh Devices**: Click "Refresh Devices" button
3. **Select APK**: Right-click desired file
4. **Choose Install**: Select "Auto Install" → Device
5. **Confirm**: Installation proceeds automatically

### Manage Multiple Servers

1. **Configure Servers**: Server admin adds multiple SMB servers
2. **Select Server**: Use server dropdown in client
3. **Search Specific**: Search within specific server
4. **Compare Results**: Switch between servers to compare

## Configuration

### Client Configuration

The client stores settings in `~/.apk_finder/config.json`:

```json
{
  "server_url": "http://localhost:9301",
  "api_token": "your_token",
  "download_path": "/Users/name/Downloads/APK",
  "auto_verify_md5": true,
  "theme": "Light",
  "font_size": 14,
  "remember_window_size": true,
  "adb_path": "adb",
  "install_flags": "-r -d -t"
}
```

### Environment Variables

Alternative to settings dialog:

```env
# Server Connection
SERVER_URL=http://your-server:9301
API_TOKEN=your_secure_token

# Paths
DEFAULT_DOWNLOAD_PATH=/path/to/downloads

# UI Settings  
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
THEME=Light

# Behavior
MAX_SEARCH_RESULTS=100
DEFAULT_RESULTS_PER_PAGE=20
```

## Keyboard Shortcuts

- **Ctrl+F**: Focus search box
- **Enter**: Execute search
- **Ctrl+R**: Refresh scan
- **Ctrl+D**: Download selected file
- **Ctrl+,**: Open settings
- **F5**: Refresh file list
- **Escape**: Clear search

## Building Executable

### PyInstaller Build

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
cd client
pyinstaller --onefile --windowed \
  --name "APK Finder" \
  --icon resources/icon.ico \
  main.py

# Output in dist/
```

### Build Options

**One File**:
```bash
pyinstaller --onefile main.py
```

**With Resources**:
```bash
pyinstaller --onefile --add-data "ui;ui" main.py
```

**Debug Build**:
```bash
pyinstaller --onefile --console main.py
```

## Troubleshooting

### Connection Issues

**Cannot Connect to Server**:
1. Verify server is running
2. Check server URL in settings
3. Confirm API token is correct
4. Test with `/health` endpoint manually

**Search Returns No Results**:
1. Check server has scanned files
2. Verify search keywords
3. Try different build type filter
4. Check server logs for errors

### ADB Issues

**No Devices Detected**:
1. Install Android SDK platform-tools
2. Add ADB to system PATH
3. Enable USB debugging on device
4. Check USB cable connection
5. Verify ADB path in settings

**Installation Fails**:
1. Check ADB connection: `adb devices`
2. Verify APK file integrity
3. Try different installation flags
4. Check device storage space
5. Review ADB error messages

### UI Issues

**Interface Not Responsive**:
1. Close and restart application
2. Check system resources
3. Update PyQt5 to latest version
4. Reset settings to defaults

**Styling Problems**:
1. Check font availability
2. Try different theme
3. Adjust font size in settings
4. Clear application cache

### Performance Issues

**Slow Search**:
1. Check server performance
2. Reduce search result limits
3. Use more specific keywords
4. Check network latency

**Download Issues**:
1. Check available disk space
2. Verify download path permissions
3. Test server download endpoint
4. Check network connectivity

## Development

### Code Structure

```
client/
├── src/
│   ├── main_window.py         # Main application window
│   ├── settings_dialog.py     # Settings management
│   ├── api_client.py          # Server communication
│   ├── adb_manager.py         # Android device integration
│   └── config.py              # Configuration handling
├── ui/
│   └── styles.py              # UI styling and themes
├── resources/                 # Icons and assets
├── main.py                    # Application entry point
└── requirements.txt           # Dependencies
```

### Adding Features

**New UI Components**:
1. Add to `main_window.py`
2. Style in `ui/styles.py`
3. Connect signals and slots

**API Integration**:
1. Add methods to `api_client.py`
2. Handle async operations
3. Update UI with results

**Settings Options**:
1. Add to `settings_dialog.py`
2. Update `config.py` for persistence
3. Apply settings in main window

### Testing

```bash
# Run with debug output
python main.py --debug

# Test API connectivity
python -c "from src.api_client import api_client; import asyncio; print(asyncio.run(api_client.health_check()))"

# Test ADB functionality  
python -c "from src.adb_manager import adb_manager; print(adb_manager.get_connected_devices())"
```

## Support

For issues and support:
1. Check this documentation
2. Review error messages and logs
3. Test server connectivity
4. Verify ADB setup for device issues
5. Create issue on GitHub with details