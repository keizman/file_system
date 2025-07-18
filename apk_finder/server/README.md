# APK Finder Server

The server component of APK Finder that handles file scanning, indexing, and API services.

## Features

- **Multi-Server SMB Support**: Connect to multiple SMB file servers
- **Intelligent Scanning**: Incremental scanning with change detection
- **Redis Caching**: Fast data storage and retrieval
- **RESTful API**: Complete API for client applications
- **Background Tasks**: Automated scanning and cleanup
- **Comprehensive Logging**: Detailed operation logs

## Quick Start

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start Server**:
```bash
python main.py
```

## Configuration

### Environment Variables (.env)

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

# Timing Configuration
UPDATE_INTERVAL=5m          # Scan interval
TEMP_CLEAN_INTERVAL=30m     # Temp file cleanup interval

# Server Configuration
SERVER_PORT=9301
LOG_LEVEL=INFO
API_TOKEN=your_secure_token_here
```

### File Server Setup

Each file server is configured with:
- **Path**: SMB network path (e.g., `\\server\share\path`)
- **Username**: SMB authentication username
- **Password**: SMB authentication password

You can configure multiple servers by incrementing the number:
```env
FILE_SERVER_1=\\server1\share
FILE_SERVER_1_USER=user1
FILE_SERVER_1_PASS=pass1

FILE_SERVER_2=\\server2\share
FILE_SERVER_2_USER=user2
FILE_SERVER_2_PASS=pass2
```

## Architecture

### Components

1. **API Layer** (`api.py`): FastAPI-based REST API
2. **Scanner Service** (`scanner.py`): APK file scanning and indexing
3. **Redis Client** (`redis_client.py`): Data storage and caching
4. **SMB Client** (`smb_client.py`): File server connectivity
5. **Configuration** (`config.py`): Settings management

### Data Flow

```
SMB Servers → Scanner → Redis → API → Clients
```

### Redis Data Structure

Files are stored in Redis with the following structure:

```json
{
  "key": "apk_finder:server_1:App_MyApp",
  "value": {
    "files": [
      {
        "relative_path": "\\App_MyApp\\release\\myapp.apk",
        "file_name": "myapp.apk",
        "file_size": 104857600,
        "created_time": "2025-01-17T18:00:00",
        "server_prefix": "\\\\192.168.1.39\\build\\Apps",
        "build_type": "release",
        "download_time": 5,
        "md5": "abc123..."
      }
    ],
    "last_updated": "2025-01-17T18:00:00"
  }
}
```

Metadata is stored separately:
```json
{
  "key": "apk_finder:server_1:meta",
  "value": {
    "App_MyApp": {
      "subdir_count": 15,
      "last_scan": "2025-01-17T18:00:00",
      "files_count": 25
    }
  }
}
```

## API Endpoints

### Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer YOUR_API_TOKEN
```

### POST /api/search
Search for APK files.

**Request**:
```json
{
  "keyword": "myapp",
  "server": "server_1",      // optional
  "build_type": "release",   // release|debug|combine
  "limit": 10,
  "offset": 0
}
```

**Response**:
```json
{
  "code": 200,
  "data": {
    "total": 50,
    "items": [...],
    "limit": 10,
    "offset": 0
  }
}
```

### POST /api/refresh
Trigger manual scan refresh.

**Parameters**:
- `server` (optional): Specific server to refresh

**Response**:
```json
{
  "code": 200,
  "message": "Started refresh for all servers"
}
```

### GET /api/download
Download APK file.

**Parameters**:
- `path`: Relative file path
- `server`: Server identifier

**Response**: File download stream

### GET /api/file/info
Get file information.

**Parameters**:
- `path`: Relative file path
- `server`: Server identifier

**Response**:
```json
{
  "path": "\\path\\to\\file.apk",
  "size": 104857600,
  "modified_time": "2025-01-17T18:00:00",
  "md5": "abc123...",
  "exists": true
}
```

### GET /api/status
Get system status.

**Response**:
```json
{
  "last_scan_time": "2025-01-17T18:00:00",
  "total_files": 1000,
  "scanning": false,
  "servers_status": {
    "server_1": {
      "files_count": 500,
      "last_scan": "2025-01-17T18:00:00"
    }
  },
  "redis_status": "connected"
}
```

### GET /api/servers
Get configured servers.

**Response**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "server_1",
      "display_name": "Server 1",
      "path": "\\\\192.168.1.39\\build\\Apps"
    }
  ]
}
```

### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-17T18:00:00Z",
  "services": {
    "redis": "connected",
    "scanner": "running"
  }
}
```

## Scanning Algorithm

### Incremental Scanning

The server uses an intelligent incremental scanning algorithm:

1. **Directory Enumeration**: List all second-level directories
2. **Change Detection**: Count subdirectories in each folder
3. **Comparison**: Compare current count with cached count in Redis
4. **Conditional Scan**: Only scan directories with changed counts
5. **Update Cache**: Store new counts and file data in Redis

This approach dramatically reduces scan time for large file collections.

### File Processing

For each directory that needs scanning:

1. **Recursive Traversal**: Walk through all subdirectories
2. **APK Detection**: Filter for `.apk` files only
3. **Metadata Extraction**: Collect file size, timestamps, paths
4. **Build Type Detection**: Determine release/debug from path
5. **Redis Storage**: Store structured data in Redis

## Deployment

### Production Setup

1. **Environment Configuration**:
```bash
# Production .env
LOG_LEVEL=WARNING
UPDATE_INTERVAL=10m
TEMP_CLEAN_INTERVAL=1h
```

2. **Process Management** (systemd):
```ini
[Unit]
Description=APK Finder Server
After=network.target redis.service

[Service]
Type=simple
User=apkfinder
WorkingDirectory=/opt/apk-finder/server
ExecStart=/opt/apk-finder/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Reverse Proxy** (nginx):
```nginx
server {
    listen 80;
    server_name apkfinder.company.com;
    
    location / {
        proxy_pass http://127.0.0.1:9301;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 9301

CMD ["python", "main.py"]
```

## Monitoring

### Logs

Logs are written to:
- Console: Structured logs with timestamps
- File: `logs/apk_finder.log` with rotation

Log levels:
- `DEBUG`: Detailed operation info
- `INFO`: General operation status
- `WARNING`: Minor issues
- `ERROR`: Serious problems

### Metrics

Monitor these key metrics:
- API response times
- Scan duration and frequency
- Redis memory usage
- SMB connection health
- Error rates

### Health Checks

The `/health` endpoint provides:
- Overall service status
- Redis connectivity
- Scanner state
- Timestamp information

## Troubleshooting

### Common Issues

**Redis Connection Failed**:
```bash
# Check Redis status
redis-cli ping

# Verify connection string
redis-cli -u "redis://user:pass@host:port/db"
```

**SMB Authentication Failed**:
- Verify credentials in .env
- Test SMB access manually
- Check network connectivity
- Ensure SMB ports are open (445)

**Scanner Not Running**:
- Check logs for errors
- Verify Redis connectivity
- Test SMB server accessibility
- Check directory permissions

**High Memory Usage**:
- Monitor Redis memory usage
- Adjust scan frequency
- Consider data cleanup policies
- Check for memory leaks

### Performance Tuning

**Large File Collections**:
- Increase `UPDATE_INTERVAL`
- Use Redis clustering
- Implement data partitioning
- Monitor scan performance

**High API Load**:
- Use Redis connection pooling
- Implement response caching
- Add rate limiting
- Use async request handling

## Development

### Running in Development

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Run with auto-reload
uvicorn src.api:app --reload --host 0.0.0.0 --port 9301

# Run tests
pytest tests/
```

### Code Structure

```
server/
├── src/
│   ├── api.py              # FastAPI routes and middleware
│   ├── scanner.py          # Background scanning service
│   ├── redis_client.py     # Redis operations
│   ├── smb_client.py       # SMB file operations
│   └── config.py           # Configuration management
├── tests/                  # Test files
├── logs/                   # Log files
├── tmp/                    # Temporary downloads
├── main.py                 # Application entry point
└── requirements.txt        # Dependencies
```

### Adding New Features

1. **New API Endpoints**: Add to `api.py`
2. **Data Models**: Update `shared/models.py`
3. **Background Tasks**: Extend `scanner.py`
4. **Storage**: Modify `redis_client.py`
5. **File Operations**: Enhance `smb_client.py`