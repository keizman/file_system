# APK Finder Web Client

A modern web client for the APK Finder application, built with Vue 3, Vite, and Tailwind CSS.

# bug: Mi phone default browser will download failed, because it's has own strategy: go to built-in app to download it, but the app has install successful, theres's now shown and will not requeste again. NEXT: dump net pkg to find what he do...

## Features

- 🔍 **Search APK files** with multi-keyword support
- 🏢 **Server selection** and build type filtering  
- 📥 **Direct file downloads** with progress tracking
- 📋 **Copy file paths** (SMB/HTTP) to clipboard
- 📱 **Auto install disabled** (not available in web version)
- 🌓 **Theme support** (Light/Dark mode ready)
- 📊 **Connection status** monitoring
- 📝 **Recent downloads** tracking

## Layout Preservation

This web client preserves the original PyQt5 layout structure:

- **Header**: Title, refresh, and settings controls
- **Server Selection**: Toggle between different file servers
- **Build Type Selection**: Release, Debug, Combine filters
- **Search Bar**: Multi-keyword search with | separator
- **File List**: Tabular view with sortable columns
- **Download Panel**: Download actions and recent files
- **Status Bar**: Connection status and system info

## Key Differences from Desktop Client

- ✅ **Download files** directly through browser
- ❌ **Auto install disabled** - ADB functionality not available in web
- ✅ **Same API endpoints** and authentication
- ✅ **Responsive design** for mobile/tablet support
- ✅ **Modern web UI** with Tailwind CSS styling
- ✅ **Enhanced clipboard support** with fallbacks for older browsers

## Known Issues & Solutions

### Chinese Characters in File Paths
**Issue**: Files with Chinese characters in paths may fail to download due to server-side encoding issues.

**Solution**: 
1. Use the **📋 SMB Path** or **🔗 HTTP Path** copy buttons
2. Download manually through file explorer or direct HTTP access
3. The web client provides helpful error messages and fallback options

### Clipboard Access
**Issue**: Some browsers may block clipboard access due to security policies.

**Solution**: The web client includes automatic fallback mechanisms:
- Primary: `navigator.clipboard.writeText()` (modern browsers)
- Fallback: `document.execCommand('copy')` (older browsers)
- Manual: Error messages show the path for manual copying

## Development Setup

### Prerequisites

- Node.js 16+ and npm
- Running APK Finder server on port 9301

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Configuration

The web client is configured to proxy API requests to the APK Finder server:

- **Development**: `http://localhost:3000` → `http://localhost:9301`
- **API Token**: Uses same token as desktop client (`cs`)
- **Endpoints**: All `/api/*` and `/health` requests are proxied

## API Integration

Uses the same FastAPI endpoints as the desktop client:

- `POST /api/search` - Search APK files
- `GET /api/download` - Download files with streaming
- `POST /api/refresh` - Trigger server scan
- `GET /api/servers` - Get available servers
- `GET /health` - Health check

## Browser Compatibility

- Modern browsers with ES2020+ support
- Chrome 80+, Firefox 80+, Safari 14+, Edge 80+
- Progressive Web App features available

## Deployment

### Static Hosting

```bash
npm run build
# Deploy dist/ folder to any static hosting service
```

### Use nginx: set your builded index.html path after root

```
    server {
        listen 3001; # 监听 3001 端口
        server_name localhost; # 服务器名称，可以替换为你的域名或 IP 地址

        # 定义网站的根目录，Nginx 将在此目录中查找文件
        root /opt/file_system/apk_finder/web_client/dist;

        # 处理根路径 "/" 的请求
        location / {
            # 尝试查找 index.html 文件，如果找不到则返回 404
            try_files $uri $uri/ /index.html;
        }

        # 处理静态文件请求 (例如 CSS, JS, 图片等在 assets 目录下的文件)
        location /assets/ {
            # 禁用目录列表，防止直接访问目录内容
            autoindex off;
            # 设置静态文件的缓存时间，这里设置为 30 天
            expires 30d;
            # 开启 gzip 压缩以减少传输大小
            gzip on;
            gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
            gzip_comp_level 6; # 压缩级别
            gzip_vary on;
        }
        location /api/ {
            proxy_pass http://localhost:9301/api/; # 将请求转发到上面定义的 upstream
            proxy_set_header Host $host; # 转发原始 Host 头
            proxy_set_header X-Real-IP $remote_addr; # 转发客户端真实 IP
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; # 转发 X-Forwarded-For 头
            proxy_set_header X-Forwarded-Proto $scheme; # 转发原始协议 (http/https)

            # 如果后端 API 期望处理 POST 请求体，这些是必要的
            proxy_request_buffering off; # 关闭请求缓冲，对于流式上传等场景有用
            # 如果有大文件上传，可能需要调整 client_max_body_size
            client_max_body_size 10M; # 允许的最大请求体大小，根据需要调整
        }


        # 错误页面配置
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root html; # 默认 Nginx 错误页面的位置
        }
    }
```


### Docker

```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
```

### Reverse Proxy

Configure your reverse proxy to serve the web client and proxy API requests to the APK Finder server.

## File Downloads

Downloads are handled through the browser's native download functionality:

1. Files are streamed through the `/api/download` endpoint
2. Progress tracking shows download percentage
3. Files are saved to the browser's default download location
4. Large files supported with 5-minute timeout

## Development Notes

- **Vue 3 Composition API** for reactive state management
- **Tailwind CSS** for utility-first styling
- **Axios** for HTTP client with request/response interceptors
- **Vite** for fast development and optimized builds

## Production Considerations

- Configure proper CORS headers on the server
- Use HTTPS in production environments
- Set appropriate API timeouts for large file downloads
- Consider implementing user authentication if needed