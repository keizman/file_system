# APK Finder Deployment Guide

This guide covers deploying the APK Finder system in production environments.

## System Requirements

### Server Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.8+
- **Memory**: 4GB+ RAM
- **Storage**: 10GB+ (for logs and temporary files)
- **Redis**: 6.0+
- **Network**: Access to SMB file servers

### Client Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Python**: 3.8+ (for source install)
- **Memory**: 2GB+ RAM
- **Network**: HTTP access to server

## Production Server Deployment

### 1. Environment Setup

```bash
# Create user
sudo useradd -m -s /bin/bash apkfinder
sudo mkdir -p /opt/apk-finder
sudo chown apkfinder:apkfinder /opt/apk-finder

# Switch to user
sudo su - apkfinder
cd /opt/apk-finder

# Clone project
git clone <repository-url> .
cd server
```

### 2. Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production dependencies
pip install gunicorn supervisor
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Production `.env`:
```env
# File Servers
FILE_SERVER_1=\\192.168.1.39\build\Apps
FILE_SERVER_1_USER=smbuser
FILE_SERVER_1_PASS=secure_password

FILE_SERVER_2=\\192.168.1.37\yw\apks
FILE_SERVER_2_USER=yw
FILE_SERVER_2_PASS=another_secure_password

# Redis
REDIS_CONN_STRING=redis://default:redis_password@localhost:6379/0

# Performance
UPDATE_INTERVAL=10m
TEMP_CLEAN_INTERVAL=1h

# Server
SERVER_PORT=9301
LOG_LEVEL=WARNING
API_TOKEN=production_secure_token_here
```

### 4. Redis Setup

```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
```

Redis configuration:
```
# Security
requirepass your_redis_password
bind 127.0.0.1

# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
```

```bash
# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 5. Systemd Service

Create `/etc/systemd/system/apk-finder.service`:
```ini
[Unit]
Description=APK Finder Server
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=apkfinder
Group=apkfinder
WorkingDirectory=/opt/apk-finder/server
Environment=PATH=/opt/apk-finder/server/venv/bin
ExecStart=/opt/apk-finder/server/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/apk-finder

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable apk-finder
sudo systemctl start apk-finder

# Check status
sudo systemctl status apk-finder
sudo journalctl -u apk-finder -f
```

### 6. Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo apt install nginx
```

Create `/etc/nginx/sites-available/apk-finder`:
```nginx
server {
    listen 80;
    server_name apkfinder.yourcompany.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name apkfinder.yourcompany.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/apkfinder.crt;
    ssl_certificate_key /etc/ssl/private/apkfinder.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:9301;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Large file downloads
    location /api/download {
        proxy_pass http://127.0.0.1:9301;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Extended timeouts for downloads
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Disable buffering for streaming
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:9301;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/apk-finder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL Certificate

Using Let's Encrypt:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d apkfinder.yourcompany.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 8. Firewall Configuration

```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### 9. Monitoring

Create `/opt/apk-finder/monitor.sh`:
```bash
#!/bin/bash

# Health check script
URL="http://localhost:9301/health"
EMAIL="admin@yourcompany.com"

response=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $response != "200" ]; then
    echo "APK Finder health check failed: HTTP $response" | mail -s "APK Finder Alert" $EMAIL
    logger "APK Finder health check failed: HTTP $response"
fi
```

```bash
# Make executable
chmod +x /opt/apk-finder/monitor.sh

# Add to crontab
crontab -e
# Add: */5 * * * * /opt/apk-finder/monitor.sh
```

### 10. Log Rotation

Create `/etc/logrotate.d/apk-finder`:
```
/opt/apk-finder/server/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 apkfinder apkfinder
    postrotate
        systemctl reload apk-finder
    endscript
}
```

## Docker Deployment

### 1. Server Dockerfile

Create `server/Dockerfile`:
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libsmbclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -s /bin/bash apkfinder

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Change ownership
RUN chown -R apkfinder:apkfinder /app

# Switch to app user
USER apkfinder

# Expose port
EXPOSE 9301

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9301/health || exit 1

# Start application
CMD ["python", "main.py"]
```

### 2. Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis:6.2-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - apk_finder
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  apk-finder:
    build: ./server
    restart: unless-stopped
    ports:
      - "9301:9301"
    environment:
      - REDIS_CONN_STRING=redis://default:${REDIS_PASSWORD}@redis:6379/0
    env_file:
      - ./server/.env
    volumes:
      - ./server/logs:/app/logs
      - ./server/tmp:/app/tmp
    networks:
      - apk_finder
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9301/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    networks:
      - apk_finder
    depends_on:
      - apk-finder

networks:
  apk_finder:
    driver: bridge

volumes:
  redis_data:
```

### 3. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f apk-finder

# Scale if needed
docker-compose up -d --scale apk-finder=3
```

## Client Deployment

### 1. Executable Distribution

```bash
# Build Windows executable
cd client
pip install pyinstaller
pyinstaller --onefile --windowed --name "APK Finder" main.py

# Build for current platform
pyinstaller apk-finder.spec
```

### 2. Client Configuration

Pre-configure client with `client/config/default.json`:
```json
{
  "server_url": "https://apkfinder.yourcompany.com",
  "api_token": "client_token_here",
  "download_path": "~/Downloads/APK",
  "theme": "Light",
  "auto_verify_md5": true
}
```

### 3. MSI Installer (Windows)

Using WiX Toolset:
```xml
<!-- apk-finder.wxs -->
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="APK Finder" Language="1033" Version="1.0.0" 
           Manufacturer="Your Company" UpgradeCode="YOUR-GUID">
    
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine"/>
    
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed."/>
    
    <MediaTemplate EmbedCab="yes"/>
    
    <Feature Id="ProductFeature" Title="APK Finder" Level="1">
      <ComponentGroupRef Id="ProductComponents"/>
    </Feature>
  </Product>
  
  <Fragment>
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="APK Finder"/>
      </Directory>
    </Directory>
  </Fragment>
  
  <Fragment>
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainExecutable">
        <File Source="dist/APK Finder.exe"/>
      </Component>
    </ComponentGroup>
  </Fragment>
</Wix>
```

## Security Configuration

### 1. API Security

```env
# Strong API token
API_TOKEN=$(openssl rand -base64 32)

# Rate limiting (if using nginx)
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

### 2. SMB Security

- Use dedicated service accounts
- Implement SMB signing
- Restrict share permissions
- Use strong passwords

### 3. Network Security

```bash
# Firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 9301
sudo ufw deny 9301
```

### 4. Database Security

```bash
# Redis security
echo "requirepass $(openssl rand -base64 32)" >> /etc/redis/redis.conf
echo "rename-command FLUSHDB \"\"" >> /etc/redis/redis.conf
echo "rename-command FLUSHALL \"\"" >> /etc/redis/redis.conf
```

## Backup and Recovery

### 1. Data Backup

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/apk-finder"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Redis data
redis-cli --rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup configuration
cp /opt/apk-finder/server/.env $BACKUP_DIR/config_$DATE.env

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /opt/apk-finder/server/logs/

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.env" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 2. Recovery Procedures

```bash
# Stop service
sudo systemctl stop apk-finder

# Restore Redis data
sudo systemctl stop redis-server
cp /backup/apk-finder/redis_YYYYMMDD_HHMMSS.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb
sudo systemctl start redis-server

# Restore configuration
cp /backup/apk-finder/config_YYYYMMDD_HHMMSS.env /opt/apk-finder/server/.env

# Start service
sudo systemctl start apk-finder
```

## Performance Tuning

### 1. Redis Optimization

```bash
# /etc/redis/redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 0
```

### 2. Application Tuning

```env
# Server configuration
UPDATE_INTERVAL=15m
TEMP_CLEAN_INTERVAL=2h
```

### 3. Nginx Optimization

```nginx
# Worker processes
worker_processes auto;
worker_connections 1024;

# Gzip compression
gzip on;
gzip_types text/plain application/json application/javascript text/css;

# Caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Troubleshooting

### 1. Service Issues

```bash
# Check service status
sudo systemctl status apk-finder
sudo journalctl -u apk-finder -n 50

# Check Redis
redis-cli ping
redis-cli info memory

# Check network
netstat -tlnp | grep 9301
curl -I http://localhost:9301/health
```

### 2. Performance Issues

```bash
# Monitor resources
htop
iotop
redis-cli --latency

# Check logs
tail -f /opt/apk-finder/server/logs/apk_finder.log
tail -f /var/log/nginx/access.log
```

### 3. Common Fixes

**High Memory Usage**:
```bash
# Restart Redis to free memory
sudo systemctl restart redis-server

# Clear Redis cache
redis-cli FLUSHDB
```

**Slow Scanning**:
```bash
# Increase scan interval
echo "UPDATE_INTERVAL=30m" >> /opt/apk-finder/server/.env
sudo systemctl restart apk-finder
```

**Connection Issues**:
```bash
# Check firewall
sudo ufw status
sudo netstat -tlnp | grep 9301

# Test SMB connectivity
smbclient -L //192.168.1.39 -U username
```