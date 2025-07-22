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
import asyncio
from functools import wraps


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry failed operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}, retrying in {delay}s...")
                        if asyncio.iscoroutinefunction(func):
                            await asyncio.sleep(delay)
                        else:
                            time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator


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
    
    logger.debug(f"🔄 Request: {request.method} {request.url}")
    logger.debug(f"   Headers: {dict(request.headers)}")
    logger.debug(f"   Query params: {dict(request.query_params)}")
    logger.debug(f"   Client IP: {request.client.host}")
    
    # Process request
    response = await call_next(request)
    
    # Log response details
    process_time = time.time() - start_time
    print(f"✅ Response: {response.status_code} - {process_time:.3f}s")
    logger.debug(f"✅ Response: {response.status_code} - {process_time:.3f}s")
    
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
@retry_on_failure(max_retries=2, delay=0.5)
async def download_file(request: Request, path: str, server: str, filename: Optional[str] = None, token: str = Depends(verify_token)):
    """Download APK file with streaming and range support for Android compatibility"""
    try:
        # Validate server
        if server not in Config.FILE_SERVERS:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Get SMB client
        client = smb_manager.get_client(server)
        
        # Check if file exists and get file info first
        if not client.file_exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file size using multiple methods (critical for Android progress display)
        file_info = client.get_file_info(path)
        if not file_info.get("exists", False):
            raise HTTPException(status_code=404, detail="File not found")
        
        file_size = file_info.get("size", 0)
        size_detection_method = "file_info"
        
        # If file size is 0 or invalid, try alternative methods
        if file_size <= 0:
            logger.warning(f"File size from file_info is {file_size} for {path}, trying alternative methods")
            
            # Method 1: Try smbclient stat
            try:
                import smbclient
                # Use same path construction logic as SMB client
                server_path = Config.FILE_SERVERS[server]["path"]
                if server_path.endswith("\\"):
                    server_path = server_path[:-1]
                
                if path.startswith("\\"):
                    unc_path = f"{server_path}{path}"
                else:
                    unc_path = f"{server_path}\\{path}"
                
                # Configure smbclient
                smbclient.ClientConfig(
                    username=Config.FILE_SERVERS[server].get("username", ""),
                    password=Config.FILE_SERVERS[server].get("password", "")
                )
                
                stat_info = smbclient.stat(unc_path)
                if hasattr(stat_info, 'st_size') and stat_info.st_size > 0:
                    file_size = stat_info.st_size
                    size_detection_method = "smbclient_stat"
                    logger.info(f"Got file size via smbclient.stat: {file_size}")
                    
            except Exception as e:
                logger.warning(f"smbclient.stat failed: {e}")
            
            # Method 2: Final fallback to low-level API (only as last resort)
            if file_size <= 0:
                try:
                    _, detected_size = client.download_file_stream(path)
                    if detected_size and detected_size > 0:
                        file_size = detected_size
                        size_detection_method = "download_stream_lowlevel"
                        logger.info(f"Got file size via low-level download stream: {file_size}")
                except Exception as e:
                    logger.warning(f"Could not get file size from low-level download: {e}")
        
        # Validate final file size
        if file_size <= 0:
            logger.error(f"Could not determine file size for {path}, will proceed without Content-Length")
            file_size = None
        else:
            logger.info(f"Final file size for {path}: {file_size} bytes (method: {size_detection_method})")
        
        # Parse Range header for resumable downloads
        range_header = request.headers.get('range')
        start = 0
        end = file_size - 1 if file_size and file_size > 0 else 0
        status_code = 200
        
        if range_header and file_size and file_size > 0:
            # Parse Range: bytes=start-end
            try:
                range_match = range_header.replace('bytes=', '')
                if '-' in range_match:
                    range_start, range_end = range_match.split('-', 1)
                    if range_start:
                        start = int(range_start)
                    if range_end:
                        end = int(range_end)
                    else:
                        end = file_size - 1
                    
                    # Validate range
                    if start >= file_size or end >= file_size or start > end:
                        raise HTTPException(
                            status_code=416, 
                            detail="Requested Range Not Satisfiable",
                            headers={"Content-Range": f"bytes */{file_size}"}
                        )
                    
                    status_code = 206
                    logger.info(f"Range request: bytes {start}-{end}/{file_size}")
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid range header: {range_header}, error: {e}")
                # Ignore invalid range, serve full file
                range_header = None
        
        # Get file stream with range support
        if range_header and status_code == 206:
            try:
                # Use range-capable download method
                file_stream = client.download_file_range_stream(path, start, end)
            except Exception as e:
                logger.warning(f"Range download failed, falling back to full download: {e}")
                # Fallback to normal download and skip to start position
                file_stream = client.download_file_stream_with_skip(path, start, end)
        else:
            # Normal download without range
            try:
                # Try smbclient high-level API first (most stable)
                file_stream, _ = client.download_file_stream_smbclient(path)
            except Exception as e:
                logger.warning(f"smbclient method failed, trying low-level API: {e}")
                try:
                    # Fallback to fixed low-level API
                    file_stream, _ = client.download_file_stream(path)
                except Exception as e2:
                    logger.warning(f"Normal download failed, trying simplified method: {e2}")
                    # Final fallback to simplified method
                    try:
                        file_stream, _ = client.download_file_stream_simple(path)
                    except Exception as e3:
                        logger.error(f"All download methods failed: {e3}")
                        raise HTTPException(status_code=500, detail=f"Download failed: {e3}")
        
        # Use provided filename or extract from path
        if not filename:
            filename = os.path.basename(path)
        
        # Set up headers - handle Chinese filenames properly for Android
        import urllib.parse
        
        # Clean filename - remove path separators and special chars that may cause issues
        clean_filename = filename.replace('\\', '_').replace('/', '_').strip()
        
        # For Android compatibility, try multiple filename encoding approaches
        content_disposition_attempts = []
        
        try:
            clean_filename.encode('ascii')
            # ASCII safe, use simple format
            content_disposition_attempts.append(f'attachment; filename="{clean_filename}"')
        except UnicodeEncodeError:
            # Non-ASCII characters - use multiple fallback methods for Android compatibility
            
            # Method 1: RFC 2231 encoding (preferred)
            encoded_filename = urllib.parse.quote(clean_filename.encode('utf-8'))
            content_disposition_attempts.append(f"attachment; filename*=UTF-8''{encoded_filename}")
            
            # Method 2: Simplified ASCII fallback
            ascii_filename = clean_filename.encode('ascii', 'ignore').decode('ascii')
            if ascii_filename:
                content_disposition_attempts.append(f'attachment; filename="{ascii_filename}.apk"')
            
            # Method 3: Generic APK name as final fallback
            content_disposition_attempts.append('attachment; filename="download.apk"')
        
        # Use the first attempt as primary
        content_disposition = content_disposition_attempts[0]
        
        # Detect Android user agent for specific optimizations
        user_agent = request.headers.get('user-agent', '').lower()
        is_android = 'android' in user_agent
        is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad'])
        
        logger.info(f"Download request from: {user_agent}, is_android: {is_android}, is_mobile: {is_mobile}")
        
        # Base headers optimized for Android browsers
        headers = {
            'Content-Disposition': content_disposition,
            'Content-Type': 'application/vnd.android.package-archive',
            'Accept-Ranges': 'bytes',
            'Connection': 'keep-alive',
            'Cache-Control': 'public, max-age=0, must-revalidate',
            'Pragma': 'public',
            'X-Content-Type-Options': 'nosniff'
        }
        
        # Android-specific optimizations
        if is_android:
            # Android browsers work better with these headers
            headers.update({
                'Content-Transfer-Encoding': 'binary',
                'X-Download-Options': 'noopen',
                'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges'
            })
        
        # Set content length and range headers
        if status_code == 206:
            content_length = end - start + 1
            headers['Content-Length'] = str(content_length)
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            logger.info(f"Serving range: {start}-{end}, content-length: {content_length}")
        else:
            if file_size and file_size > 0:
                headers['Content-Length'] = str(file_size)
                logger.info(f"Serving full file, content-length: {file_size}")
            else:
                logger.warning(f"Serving file without Content-Length (size unknown)")
                # For Android compatibility, try to set a reasonable content-type
                headers['Transfer-Encoding'] = 'chunked'
        
        # Increment download count
        directory = path.split("\\")[1] if "\\" in path else ""
        redis_client.increment_download_count(server, directory, path)
        
        logger.info(f"Starting streaming download: {path} -> {filename} (status: {status_code})")
        
        # Wrap file stream with error handling to prevent server crashes
        def safe_file_stream():
            try:
                yield from file_stream
                logger.info(f"Completed streaming download: {path}")
            except Exception as stream_error:
                logger.error(f"Stream error during download of {path}: {stream_error}")
                # Don't re-raise here as it would crash the connection
                # The client will detect the incomplete download
                return
        
        return StreamingResponse(
            safe_file_stream(),
            status_code=status_code,
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


@app.get("/api/download/check")
async def check_download_capability(path: str, server: str, token: str = Depends(verify_token)):
    """Check if file can be downloaded and get download info"""
    try:
        # Validate server
        if server not in Config.FILE_SERVERS:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Get SMB client
        client = smb_manager.get_client(server)
        
        # Check file existence and get info
        if not client.file_exists(path):
            return {
                "code": 404,
                "downloadable": False,
                "error": "File not found"
            }
        
        # Get file info
        file_info = client.get_file_info(path)
        
        # Test download capability without actually opening the file stream
        download_methods = []
        try:
            # Test file accessibility using stat instead of opening stream
            import smbclient
            server_path = Config.FILE_SERVERS[server]["path"]
            if server_path.endswith("\\"):
                server_path = server_path[:-1]
            if path.startswith("\\"):
                unc_path = f"{server_path}{path}"
            else:
                unc_path = f"{server_path}\\{path}"
            
            # Configure credentials
            smbclient.ClientConfig(
                username=Config.FILE_SERVERS[server].get("username", ""),
                password=Config.FILE_SERVERS[server].get("password", "")
            )
            
            # Just check file stats, don't open the file
            file_stat = smbclient.stat(unc_path)
            size = file_stat.st_size
            
            download_methods.append({
                "method": "smbclient", 
                "available": True, 
                "can_get_size": True,
                "size": size
            })
        except Exception as e:
            download_methods.append({
                "method": "smbclient", 
                "available": False, 
                "error": str(e)
            })
        
        try:
            # Test low-level API
            _, size = client.download_file_stream(path)
            download_methods.append({
                "method": "low_level", 
                "available": True, 
                "can_get_size": size is not None,
                "size": size
            })
        except Exception as e:
            download_methods.append({
                "method": "low_level", 
                "available": False, 
                "error": str(e)
            })
        
        return {
            "code": 200,
            "downloadable": True,
            "file_info": file_info,
            "download_methods": download_methods,
            "supports_range": True,  # We always support range through our implementation
            "recommended_chunk_size": 65536  # 64KB
        }
        
    except Exception as e:
        logger.error(f"Error checking download capability: {e}")
        return {
            "code": 500,
            "downloadable": False,
            "error": str(e)
        }


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