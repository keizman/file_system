import os
import tempfile
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from config import Config
from redis_client import redis_client
from scanner import scanner
from smb_client import smb_manager
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
async def download_file(path: str, server: str, token: str = Depends(verify_token)):
    """Download APK file"""
    try:
        # Validate server
        if server not in Config.FILE_SERVERS:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Get SMB client
        client = smb_manager.get_client(server)
        
        # Check if file exists
        if not client.file_exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate temporary file path
        filename = os.path.basename(path)
        temp_file = os.path.join(Config.TEMP_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
        
        # Download file
        if not client.download_file(path, temp_file):
            raise HTTPException(status_code=500, detail="Failed to download file")
        
        # Calculate MD5 and update in Redis
        md5_hash = calculate_md5(temp_file)
        if md5_hash:
            # Find directory from path
            directory = path.split("\\")[1] if "\\" in path else ""
            redis_client.update_file_md5(server, directory, path, md5_hash)
        
        # Increment download count
        directory = path.split("\\")[1] if "\\" in path else ""
        redis_client.increment_download_count(server, directory, path)
        
        logger.info(f"File downloaded: {path} -> {temp_file}")
        
        return FileResponse(
            path=temp_file,
            filename=filename,
            media_type='application/vnd.android.package-archive'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
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