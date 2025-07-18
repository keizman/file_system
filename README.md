# APK Finder

A powerful client-server application for managing and searching APK files across multiple file servers with SMB support.

## Features

### Server Features
- 🔍 **Intelligent Scanning**: Incremental scanning algorithm that only scans changed directories
- 🌐 **Multi-Server Support**: Connect to multiple SMB file servers simultaneously  
- ⚡ **Redis Caching**: Fast search and data retrieval with Redis backend
- 📊 **RESTful API**: Complete API for search, download, and file management
- 🔄 **Auto-Refresh**: Configurable automatic scanning intervals
- 📝 **Comprehensive Logging**: Detailed logging with loguru

### Client Features
- 🎨 **Modern UI**: Beautiful PyQt5 interface with custom styling
- 🔍 **Advanced Search**: Multi-keyword search with build type filtering
- 📱 **ADB Integration**: One-click APK installation to connected devices
- ⬇️ **Smart Downloads**: MD5 verification and progress tracking
- 📋 **Context Menus**: Copy SMB/HTTP paths, file details, and more
- ⚙️ **Rich Settings**: Comprehensive configuration management
- 🔗 **Real-time Status**: Connection monitoring and system status

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  File Server 1  │     │  File Server 2  │
│ 192.168.1.39    │     │ 192.168.1.37    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │   Server    │
              │  (FastAPI)  │
              │   + Redis   │
              └──────┬──────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼────┐ ┌───▼────┐
    │Client 1 │ │Client 2│ │Client 3│
    │(PyQt5)  │ │(PyQt5) │ │(PyQt5) │
    └─────────┘ └────────┘ └────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- Redis server
- SMB file servers with APK files

### Server Setup

1. **Clone and setup server**:
```bash
cd apk_finder/server
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start the server**:
```bash
python main.py
```

### Client Setup

1. **Setup client**:
```bash
cd apk_finder/client
pip install -r requirements.txt
```

2. **Configure client** (optional):
Create `client/.env`:
```env
SERVER_URL=http://your-server:9301
API_TOKEN=your_token
DEFAULT_DOWNLOAD_PATH=/path/to/downloads
```

3. **Run client**:
```bash
python main.py
```

## Configuration

### Server Configuration (.env)

```env
# File Server Configuration
FILE_SERVER_1=\\192.168.1.39\build\Apps
FILE_SERVER_1_USER=smbuser
FILE_SERVER_1_PASS=123456

FILE_SERVER_2=\\192.168.1.37\yw\apks
FILE_SERVER_2_USER=yw
FILE_SERVER_2_PASS=yw123456

# Redis Configuration
REDIS_CONN_STRING=redis://default:123456@192.168.1.118:63791/0

# Update Configuration
UPDATE_INTERVAL=5m
TEMP_CLEAN_INTERVAL=30m

# Server Configuration
SERVER_PORT=9301
LOG_LEVEL=INFO
API_TOKEN=your_secure_token_here
```

### Client Configuration

The client uses a settings dialog for configuration, but you can also use environment variables:

```env
SERVER_URL=http://localhost:9301
API_TOKEN=your_token
DEFAULT_DOWNLOAD_PATH=~/Downloads/APK
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
```

## API Documentation

### Authentication
All API endpoints require Bearer token authentication:
```
Authorization: Bearer your_token
```

### Endpoints

#### Search APK Files
```http
POST /api/search
Content-Type: application/json

{
  "keyword": "myapp",
  "server": "server_1",
  "build_type": "release",
  "limit": 10,
  "offset": 0
}
```

#### Download File
```http
GET /api/download?path=/path/to/file.apk&server=server_1
```

#### Refresh Scan
```http
POST /api/refresh
```

#### System Status
```http
GET /api/status
```

#### Health Check
```http
GET /health
```

## Usage

### Basic Search
1. Start the client application
2. Enter search keywords in the search box
3. Use `|` to separate multiple keywords (e.g., `myapp|release`)
4. Select build type: Release, Debug, or Combine
5. Browse results in the file table

### File Management
- **Right-click** on files for context menu
- **Copy SMB Path**: Get SMB network path
- **Copy HTTP Path**: Get HTTP download URL
- **Download**: Save file locally with progress tracking
- **Auto Install**: Install directly to connected Android devices

### ADB Integration
1. Enable USB debugging on your Android device
2. Connect device via USB
3. Click "Refresh Devices" to detect connected devices
4. Right-click APK → Auto Install → Select device

## Development

### Project Structure
```
apk_finder/
├── server/
│   ├── src/
│   │   ├── api.py          # FastAPI application
│   │   ├── scanner.py      # APK scanning service
│   │   ├── redis_client.py # Redis data layer
│   │   ├── smb_client.py   # SMB file operations
│   │   └── config.py       # Configuration management
│   ├── main.py             # Server entry point
│   └── requirements.txt    # Server dependencies
├── client/
│   ├── src/
│   │   ├── main_window.py     # Main UI window
│   │   ├── settings_dialog.py # Settings interface
│   │   ├── api_client.py      # Server API client
│   │   ├── adb_manager.py     # ADB integration
│   │   └── config.py          # Client configuration
│   ├── ui/
│   │   └── styles.py          # UI styling
│   ├── main.py                # Client entry point
│   └── requirements.txt       # Client dependencies
└── shared/
    ├── models.py              # Shared data models
    └── utils.py               # Shared utilities
```

### Running Tests
```bash
# Server tests
cd server
python -m pytest tests/

# Client tests  
cd client
python -m pytest tests/
```

### Building Client
```bash
cd client
pyinstaller --onefile --windowed main.py
```

## Features in Detail

### Incremental Scanning
The server uses an intelligent scanning algorithm:
- Tracks directory modification counts in Redis
- Only scans directories that have changed
- Dramatically improves scan performance for large file collections

### Multi-keyword Search
Search supports complex queries:
- `myapp` - Simple search
- `myapp|release` - Must contain both "myapp" AND "release"
- `debug|v1.2` - Must contain both "debug" AND "v1.2"

### ADB Integration
Seamless Android device integration:
- Automatic device detection
- Multi-device support with device selection
- Configurable installation flags (`-r -d -t`)
- Installation status feedback

### Modern UI
Beautiful, responsive interface:
- Custom styling with modern color scheme
- Responsive layouts and proper spacing
- Progress indicators and status updates
- Context menus and keyboard shortcuts

## Troubleshooting

### Server Issues

**Redis Connection Failed**:
```bash
# Check Redis is running
redis-cli ping

# Verify connection string in .env
REDIS_CONN_STRING=redis://localhost:6379/0
```

**SMB Connection Failed**:
- Verify SMB server is accessible
- Check credentials in .env file
- Ensure SMB shares are properly configured

**Scanner Not Working**:
- Check log files in `server/logs/`
- Verify file server paths are accessible
- Check Redis connectivity

### Client Issues

**Cannot Connect to Server**:
- Verify server is running on correct port
- Check server URL in client settings
- Verify API token matches server configuration

**ADB Not Working**:
- Install Android SDK platform-tools
- Enable USB debugging on device
- Check ADB path in client settings

**Download Failures**:
- Check available disk space
- Verify download directory permissions
- Check server logs for errors

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review server logs for error details