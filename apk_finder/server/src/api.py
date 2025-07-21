import os
import tempfile
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import time
from .config import Config
from .redis_client import redis_client
from .scanner import scanner
from .smb_client import smb_manager
from shared.models import SearchRequest, SearchResponse, SystemStatus, DownloadRequest, FileInfo
from shared.utils import calculate_md5


# Initialize FastAPI app
app = FastAPI(
    title="APK Finder Server",
    description="Server for managing and searching APK files across multiple file servers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Log request details - use both print and logger to ensure visibility
    print(f"🔄 Request: {request.method} {request.url}")
    print(f"   Headers: {dict(request.headers)}")
    print(f"   Query params: {dict(request.query_params)}")
    print(f"   Client IP: {request.client.host}")
    
    logger.warning(f"🔄 Request: {request.method} {request.url}")
    logger.warning(f"   Headers: {dict(request.headers)}")
    logger.warning(f"   Query params: {dict(request.query_params)}")
    logger.warning(f"   Client IP: {request.client.host}")
    
    # Process request
    response = await call_next(request)
    
    # Log response details
    process_time = time.time() - start_time
    print(f"✅ Response: {response.status_code} - {process_time:.3f}s")
    logger.warning(f"✅ Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# Security
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token"""
    if credentials.credentials != Config.API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting APK Finder Server")
    scanner.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down APK Finder Server")
    scanner.stop()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "APK Finder Server", "version": "1.0.0"}


@app.post("/api/search", response_model=SearchResponse)
async def search_apk_files(request: SearchRequest, token: str = Depends(verify_token)):
    """Search for APK files"""
    try:
        files, total = redis_client.search_apk_files(
            keyword=request.keyword,
            server=request.server,
            build_type=request.build_type,
            limit=request.limit,
            offset=request.offset
        )
        
        return SearchResponse(
            code=200,
            data={
                "total": total,
                "items": [file.model_dump() for file in files],
                "limit": request.limit,
                "offset": request.offset
            }
        )
        
    except Exception as e:
        logger.error(f"Error searching APK files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refresh")
async def refresh_scan(background_tasks: BackgroundTasks, 
                      server: Optional[str] = None, 
                      token: str = Depends(verify_token)):
    """Trigger a manual scan refresh"""
    try:
        if server:
            background_tasks.add_task(scanner.force_scan_server, server)
            message = f"Started refresh for server: {server}"
        else:
            background_tasks.add_task(scanner.force_scan_all)
            message = "Started refresh for all servers"
        
        return {"code": 200, "message": message}
        
    except Exception as e:
        logger.error(f"Error triggering refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download")
async def download_file(path: str, server: str, filename: Optional[str] = None, token: str = Depends(verify_token)):
    """Download APK file with streaming"""
    try:
        # Validate server
        if server not in Config.FILE_SERVERS:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Get SMB client
        client = smb_manager.get_client(server)
        
        # Check if file exists
        if not client.file_exists(path):
            raise HTTPException(status_code=404, detail="File not found")

        try:
            # Try smbclient high-level API first (most stable)
            file_stream, file_size = client.download_file_stream_smbclient(path)
        except Exception as e:
            logger.warning(f"smbclient method failed, trying low-level API: {e}")
            try:
                # Fallback to fixed low-level API
                file_stream, file_size = client.download_file_stream(path)
            except Exception as e2:
                logger.warning(f"Normal download failed, trying simplified method: {e2}")
                # Final fallback to simplified method
                try:
                    file_stream, file_size = client.download_file_stream_simple(path)
                except Exception as e3:
                    logger.error(f"All download methods failed: {e3}")
                    raise HTTPException(status_code=500, detail=f"Download failed: {e3}")
        
        # Use provided filename or extract from path
        if not filename:
            filename = os.path.basename(path)
        
        # Set up headers - handle Chinese filenames properly
        import urllib.parse
        
        # Try to encode filename as ASCII first
        try:
            filename.encode('ascii')
            # ASCII safe, use simple format
            content_disposition = f'attachment; filename="{filename}"'
        except UnicodeEncodeError:
            # Contains non-ASCII characters, use RFC 2231 encoding
            encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
            content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
        
        headers = {
            'Content-Disposition': content_disposition,
            'Content-Type': 'application/vnd.android.package-archive'
        }
        
        if file_size is not None:
            headers['Content-Length'] = str(file_size)
        
        # Increment download count
        directory = path.split("\\")[1] if "\\" in path else ""
        redis_client.increment_download_count(server, directory, path)
        
        logger.info(f"Starting streaming download: {path} -> {filename}")
        
        return StreamingResponse(
            file_stream,
            headers=headers,
            media_type='application/vnd.android.package-archive'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file/info", response_model=FileInfo)
async def get_file_info(path: str, server: str, token: str = Depends(verify_token)):
    """Get file information"""
    try:
        # Validate server
        if server not in Config.FILE_SERVERS:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Get SMB client
        client = smb_manager.get_client(server)
        
        # Get file info
        file_info = client.get_file_info(path)
        
        if not file_info.get("exists", False):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileInfo(
            path=path,
            size=file_info["size"],
            modified_time=file_info["modified_time"],
            exists=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status", response_model=SystemStatus)
async def get_system_status(token: str = Depends(verify_token)):
    """Get system status"""
    try:
        # Get Redis status
        redis_status = redis_client.get_system_status()
        
        # Get scanner status
        scan_status = scanner.get_scan_status()
        
        # Combine status information
        status = SystemStatus(
            last_scan_time=datetime.fromisoformat(redis_status["last_scan_time"]) if redis_status.get("last_scan_time") else None,
            total_files=redis_status.get("total_files", 0),
            scanning=scan_status["scanning"],
            servers_status=redis_status.get("servers_status", {}),
            redis_status="connected" if redis_status.get("redis_connected") else "disconnected"
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/servers")
async def get_servers(token: str = Depends(verify_token)):
    """Get list of configured servers"""
    try:
        servers = []
        for server_name, config in Config.FILE_SERVERS.items():
            servers.append({
                "name": server_name,
                "display_name": config["name"],
                "path": config["path"]
            })
        
        return {"code": 200, "data": servers}
        
    except Exception as e:
        logger.error(f"Error getting servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_client.client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": "connected",
                "scanner": "running" if scanner.scheduler.running else "stopped"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.SERVER_PORT)