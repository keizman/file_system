# APK Finder Quick Start Guide

## Prerequisites

- Python 3.8+
- Redis server
- Access to SMB file servers with APK files

## Installation

### Option 1: Automatic Installation (Recommended)

```bash
# Clone/download the project
cd apk_finder

# Install all dependencies automatically
python install_dependencies.py
```

### Option 2: Manual Installation

```bash
# Install server dependencies
cd server
pip install -r requirements.txt

# Install client dependencies  
cd ../client
pip install -r requirements.txt
```

## Quick Setup

### 1. Configure Server

```bash
cd server
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Your SMB file servers
FILE_SERVER_1=\\192.168.1.39\build\Apps
FILE_SERVER_1_USER=your_username
FILE_SERVER_1_PASS=your_password

# Redis connection
REDIS_CONN_STRING=redis://localhost:6379/0

# API token (default is 'cs')
API_TOKEN=cs
```

### 2. Start Redis

```bash
# Ubuntu/Debian
sudo systemctl start redis-server

# Windows (if using Redis for Windows)
redis-server

# macOS (with Homebrew)
brew services start redis
```

### 3. Start Server

```bash
cd server
python main.py
```

You should see:
```
INFO: Starting APK Finder Server
INFO: Server configuration:
INFO:   Port: 9301
INFO:   API Token: cs
INFO: Starting server at http://0.0.0.0:9301
```

### 4. Start Client

```bash
cd client
python main.py
```

## First Use

1. **Server Setup**: The server will automatically start scanning your configured SMB servers
2. **Client Connection**: The client will connect to `http://localhost:9301` by default
3. **Search Files**: Use the search box to find APK files
4. **Download/Install**: Right-click files for download and install options

## Default Configuration

- **Server URL**: `http://localhost:9301`
- **API Token**: `cs` (for both server and client)
- **Download Path**: `~/Downloads/APK`
- **Default Search**: Shows latest 10 release files

## Troubleshooting

### Server Won't Start

**Redis Connection Error**:
```bash
# Check if Redis is running
redis-cli ping
# Should return "PONG"
```

**SMB Connection Error**:
- Verify SMB server paths in `.env`
- Check username/password credentials
- Ensure network access to file servers

### Client Won't Connect

**Connection Refused**:
- Verify server is running on port 9301
- Check if firewall is blocking the connection
- Try: `curl http://localhost:9301/health`

**Wrong API Token**:
- Both server and client use 'cs' by default
- Check `.env` files if you changed the token

### No Files Found

**Empty Search Results**:
- Wait for initial server scan to complete
- Check server logs for SMB connection errors
- Try clicking "Refresh" button in client

## Next Steps

1. **Configure Multiple Servers**: Add `FILE_SERVER_2`, `FILE_SERVER_3`, etc.
2. **Setup ADB**: Install Android SDK for APK installation features
3. **Production Deployment**: See `DEPLOYMENT.md` for production setup
4. **Customize Settings**: Use client Settings dialog for preferences

## Getting Help

- Check `README.md` for detailed documentation
- Review `server/logs/apk_finder.log` for server issues
- Use client Settings → Test Connection for connectivity issues