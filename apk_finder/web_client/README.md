# APK Finder Web Client

A modern web client for the APK Finder application, built with Vue 3, Vite, and Tailwind CSS.

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