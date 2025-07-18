import subprocess
import re
from typing import List, Dict, Optional


class ADBManager:
    def __init__(self):
        self.adb_path = "adb"  # Assume adb is in PATH
    
    def check_adb_available(self) -> bool:
        """Check if ADB is available"""
        try:
            result = subprocess.run([self.adb_path, "version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_connected_devices(self) -> List[Dict[str, str]]:
        """Get list of connected devices"""
        devices = []
        try:
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and '\t' in line:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2 and parts[1] == 'device':
                            serial = parts[0]
                            # Get device model
                            model = self.get_device_model(serial)
                            devices.append({
                                "serial": serial,
                                "model": model,
                                "status": "device"
                            })
        except Exception as e:
            print(f"Error getting devices: {e}")
        
        return devices
    
    def get_device_model(self, serial: str) -> str:
        """Get device model for a specific device"""
        try:
            result = subprocess.run([self.adb_path, "-s", serial, "shell", 
                                   "getprop", "ro.product.model"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return "Unknown Device"
    
    def install_apk(self, apk_path: str, device_serial: Optional[str] = None, 
                   replace: bool = True, allow_downgrade: bool = True, 
                   allow_test: bool = True) -> tuple[bool, str]:
        """Install APK to device"""
        try:
            cmd = [self.adb_path]
            
            # Add device serial if specified
            if device_serial:
                cmd.extend(["-s", device_serial])
            
            cmd.append("install")
            
            # Add installation flags
            if replace:
                cmd.append("-r")  # Replace existing app
            if allow_downgrade:
                cmd.append("-d")  # Allow version downgrade
            if allow_test:
                cmd.append("-t")  # Allow test packages
            
            cmd.append(apk_path)
            
            # Execute installation
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0 and "Success" in result.stdout
            output = result.stdout + result.stderr
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, f"Installation failed: {str(e)}"
    
    def uninstall_package(self, package_name: str, device_serial: Optional[str] = None) -> tuple[bool, str]:
        """Uninstall package from device"""
        try:
            cmd = [self.adb_path]
            
            if device_serial:
                cmd.extend(["-s", device_serial])
            
            cmd.extend(["uninstall", package_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            success = result.returncode == 0 and "Success" in result.stdout
            output = result.stdout + result.stderr
            
            return success, output
            
        except Exception as e:
            return False, f"Uninstall failed: {str(e)}"
    
    def get_installed_packages(self, device_serial: Optional[str] = None) -> List[str]:
        """Get list of installed packages"""
        try:
            cmd = [self.adb_path]
            
            if device_serial:
                cmd.extend(["-s", device_serial])
            
            cmd.extend(["shell", "pm", "list", "packages"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                packages = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        package_name = line.replace('package:', '').strip()
                        packages.append(package_name)
                return packages
                
        except Exception as e:
            print(f"Error getting packages: {e}")
        
        return []
    
    def get_package_info(self, package_name: str, device_serial: Optional[str] = None) -> Optional[Dict]:
        """Get package information"""
        try:
            cmd = [self.adb_path]
            
            if device_serial:
                cmd.extend(["-s", device_serial])
            
            cmd.extend(["shell", "dumpsys", "package", package_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout
                
                # Parse version info
                version_match = re.search(r'versionName=([^\s]+)', output)
                version_code_match = re.search(r'versionCode=([^\s]+)', output)
                
                package_info = {
                    "package_name": package_name,
                    "version_name": version_match.group(1) if version_match else "Unknown",
                    "version_code": version_code_match.group(1) if version_code_match else "Unknown"
                }
                
                return package_info
                
        except Exception as e:
            print(f"Error getting package info: {e}")
        
        return None
    
    def push_file(self, local_path: str, remote_path: str, device_serial: Optional[str] = None) -> tuple[bool, str]:
        """Push file to device"""
        try:
            cmd = [self.adb_path]
            
            if device_serial:
                cmd.extend(["-s", device_serial])
            
            cmd.extend(["push", local_path, remote_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            return success, output
            
        except Exception as e:
            return False, f"Push failed: {str(e)}"
    
    def pull_file(self, remote_path: str, local_path: str, device_serial: Optional[str] = None) -> tuple[bool, str]:
        """Pull file from device"""
        try:
            cmd = [self.adb_path]
            
            if device_serial:
                cmd.extend(["-s", device_serial])
            
            cmd.extend(["pull", remote_path, local_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            return success, output
            
        except Exception as e:
            return False, f"Pull failed: {str(e)}"
    
    def start_activity(self, package_name: str, activity_name: str = None, device_serial: Optional[str] = None) -> tuple[bool, str]:
        """Start an activity"""
        try:
            cmd = [self.adb_path]
            
            if device_serial:
                cmd.extend(["-s", device_serial])
            
            if activity_name:
                intent = f"{package_name}/{activity_name}"
            else:
                intent = package_name
            
            cmd.extend(["shell", "am", "start", "-n", intent])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            return success, output
            
        except Exception as e:
            return False, f"Start activity failed: {str(e)}"


# Global ADB manager instance
adb_manager = ADBManager()