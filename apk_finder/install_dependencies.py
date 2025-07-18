#!/usr/bin/env python3
"""
APK Finder Dependency Installer
Installs required Python packages for both server and client
"""

import subprocess
import sys
import os


def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False


def check_package(package):
    """Check if a package is already installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False


def main():
    """Main installation function"""
    print("🚀 APK Finder Dependency Installer")
    print("=" * 50)
    
    # Server dependencies
    server_deps = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "redis==5.0.1",
        "aiofiles==23.2.1",
        "smbprotocol==1.12.0",
        "APScheduler==3.10.4",
        "loguru==0.7.2",
        "python-dotenv==1.0.0",
        "httpx==0.25.2",
        "pydantic==2.5.0",
        "python-multipart==0.0.6",
        "cryptography==41.0.8"
    ]
    
    # Client dependencies  
    client_deps = [
        "PyQt5==5.15.10",
        "httpx==0.25.2",
        "QtAwesome==1.3.1",
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "aiofiles==23.2.1"
    ]
    
    print("\n📦 Installing Server Dependencies...")
    server_success = 0
    for dep in server_deps:
        if install_package(dep):
            server_success += 1
    
    print(f"\n📱 Installing Client Dependencies...")
    client_success = 0
    for dep in client_deps:
        if install_package(dep):
            client_success += 1
    
    print("\n" + "=" * 50)
    print("📊 Installation Summary:")
    print(f"Server: {server_success}/{len(server_deps)} packages installed")
    print(f"Client: {client_success}/{len(client_deps)} packages installed")
    
    if server_success == len(server_deps) and client_success == len(client_deps):
        print("\n✅ All dependencies installed successfully!")
        print("\n🎉 Next Steps:")
        print("1. Configure server: cd server && cp .env.example .env && edit .env")
        print("2. Start server: cd server && python main.py") 
        print("3. Start client: cd client && python main.py")
    else:
        print("\n⚠️ Some dependencies failed to install.")
        print("Please check the error messages above and install manually if needed.")
        
        if server_success < len(server_deps):
            print(f"\nFor server dependencies:")
            print(f"cd server && pip install -r requirements.txt")
            
        if client_success < len(client_deps):
            print(f"\nFor client dependencies:")
            print(f"cd client && pip install -r requirements.txt")


if __name__ == "__main__":
    main()