#!/usr/bin/env python3
"""
APK Finder Kivy Client - Dependency Installation Script
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"Running: {description or command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {description or command}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        print(f"  stdout: {e.stdout}")
        print(f"  stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python {version.major}.{version.minor} is not supported")
        print("  Kivy requires Python 3.8 or higher")
        return False
    print(f"✓ Python {version.major}.{version.minor} is supported")
    return True


def install_system_dependencies():
    """Install system dependencies based on platform"""
    system = platform.system().lower()
    
    if system == "linux":
        print("Installing Linux system dependencies...")
        
        # Check if we can use apt
        if run_command("which apt-get", "Checking for apt-get"):
            commands = [
                "sudo apt-get update",
                "sudo apt-get install -y python3-pip python3-dev python3-venv",
                "sudo apt-get install -y libffi-dev libssl-dev build-essential",
                "sudo apt-get install -y libmtdev-dev libgl1-mesa-dev libgles2-mesa-dev",
                "sudo apt-get install -y libdrm-dev libxkbcommon-dev libxkbcommon-x11-dev",
                "sudo apt-get install -y libxcb-xfixes0-dev libxcb-icccm4-dev libxcb-image0-dev",
                "sudo apt-get install -y libxcb-keysyms1-dev libxcb-randr0-dev libxcb-render-util0-dev",
                "sudo apt-get install -y libxcb-shape0-dev libxcb-sync-dev libxcb-xinerama0-dev",
                "sudo apt-get install -y libxcb-xkb-dev libxcb-cursor-dev"
            ]
            
            for cmd in commands:
                if not run_command(cmd):
                    print(f"Warning: Failed to run: {cmd}")
        
        # Check if we can use yum/dnf
        elif run_command("which yum", "Checking for yum"):
            commands = [
                "sudo yum install -y python3-pip python3-devel",
                "sudo yum install -y libffi-devel openssl-devel gcc gcc-c++",
                "sudo yum install -y mesa-libGL-devel mesa-libGLES-devel"
            ]
            
            for cmd in commands:
                if not run_command(cmd):
                    print(f"Warning: Failed to run: {cmd}")
    
    elif system == "darwin":  # macOS
        print("Installing macOS dependencies...")
        
        # Check if Homebrew is available
        if run_command("which brew", "Checking for Homebrew"):
            commands = [
                "brew install python3",
                "brew install libffi openssl"
            ]
            
            for cmd in commands:
                if not run_command(cmd):
                    print(f"Warning: Failed to run: {cmd}")
    
    elif system == "windows":
        print("Windows detected - dependencies should be installed via pip only")
    
    else:
        print(f"Unknown system: {system}")
        print("You may need to install dependencies manually")


def install_python_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install wheel for better dependency handling
    run_command(f"{sys.executable} -m pip install wheel", "Installing wheel")
    
    # Install requirements
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        cmd = f"{sys.executable} -m pip install -r {requirements_file}"
        if not run_command(cmd, "Installing requirements.txt"):
            print("Failed to install requirements.txt")
            return False
    else:
        print("requirements.txt not found, installing core dependencies...")
        core_deps = [
            "kivy>=2.1.0",
            "kivymd>=1.1.1",
            "httpx>=0.24.0",
            "pydantic>=2.0.0",
            "python-dotenv>=1.0.0",
            "loguru>=0.7.0",
            "python-dateutil>=2.8.0"
        ]
        
        for dep in core_deps:
            if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
                print(f"Failed to install {dep}")
                return False
    
    return True


def install_buildozer():
    """Install buildozer for Android development"""
    print("Installing buildozer for Android development...")
    
    system = platform.system().lower()
    if system != "linux":
        print("Note: Buildozer is primarily supported on Linux")
        print("For Windows, consider using WSL2")
        print("For macOS, some features may not work properly")
    
    if not run_command(f"{sys.executable} -m pip install buildozer", "Installing buildozer"):
        print("Failed to install buildozer")
        return False
    
    if not run_command(f"{sys.executable} -m pip install cython", "Installing cython"):
        print("Failed to install cython")
        return False
    
    return True


def verify_installation():
    """Verify that the installation was successful"""
    print("Verifying installation...")
    
    # Check if we can import Kivy
    try:
        import kivy
        print(f"✓ Kivy {kivy.__version__} imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Kivy: {e}")
        return False
    
    # Check if we can import other dependencies
    dependencies = [
        "kivymd",
        "httpx",
        "pydantic",
        "dotenv",
        "loguru",
        "dateutil"
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {dep}: {e}")
            return False
    
    # Check if buildozer is available
    try:
        import buildozer
        print(f"✓ buildozer imported successfully")
    except ImportError:
        print("⚠ buildozer not available (optional for desktop)")
    
    return True


def create_virtual_environment():
    """Create a virtual environment for the project"""
    print("Creating virtual environment...")
    
    venv_path = Path(__file__).parent / "venv"
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return True
    
    if not run_command(f"{sys.executable} -m venv {venv_path}", "Creating virtual environment"):
        print("Failed to create virtual environment")
        return False
    
    print(f"✓ Virtual environment created at {venv_path}")
    print("To activate it:")
    
    system = platform.system().lower()
    if system == "windows":
        print(f"  {venv_path}\\Scripts\\activate.bat")
    else:
        print(f"  source {venv_path}/bin/activate")
    
    return True


def main():
    """Main installation function"""
    print("APK Finder Kivy Client - Dependency Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Ask user what to install
    print("\nWhat would you like to install?")
    print("1. Desktop dependencies only")
    print("2. Desktop + Android development (buildozer)")
    print("3. Create virtual environment")
    print("4. All of the above")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice in ["3", "4"]:
        if not create_virtual_environment():
            print("Failed to create virtual environment")
            sys.exit(1)
        
        print("\nTo continue installation in the virtual environment:")
        print("1. Activate the virtual environment")
        print("2. Run this script again")
        return
    
    # Install system dependencies
    install_system_dependencies()
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("Failed to install Python dependencies")
        sys.exit(1)
    
    # Install buildozer if requested
    if choice in ["2", "4"]:
        if not install_buildozer():
            print("Failed to install buildozer")
            sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("Installation verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Installation completed successfully!")
    print("\nNext steps:")
    print("1. Run the application: python main.py")
    print("2. Configure server settings")
    print("3. For Android development: buildozer android debug")
    print("\nSee README.md for more detailed instructions.")


if __name__ == "__main__":
    main()