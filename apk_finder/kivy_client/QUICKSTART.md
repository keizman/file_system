# APK Finder Kivy Client - Quick Start Guide

## Desktop Quick Start

### 1. Install Dependencies
```bash
cd kivy_client
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python main.py
```

### 3. Configure Server
- Click "Settings" → "Server" tab
- Enter server URL: `http://your-server:9301`
- Enter API token (default: `cs`)
- Click "Test Connection"

### 4. Search APKs
- Select server and build type
- Enter search keywords
- Click "Search"

### 5. Download and Install
- Select file from results
- Click "Download"
- Connect Android device via USB
- Click "Auto Install"

## Android Quick Start

### 1. Prerequisites (Linux/WSL2)
```bash
# Install Java
sudo apt install openjdk-8-jdk

# Install Python tools
sudo apt install python3-pip python3-dev python3-venv

# Install build tools
sudo apt install libffi-dev libssl-dev build-essential
```

### 2. Install Buildozer
```bash
pip install buildozer
```

### 3. Prepare Resources
```bash
# Create app icon (512x512 PNG)
# Place in resources/icon.png

# Create splash screen (1280x720 PNG)  
# Place in resources/presplash.png
```

### 4. Build APK
```bash
# First time setup
buildozer init

# Build debug APK
buildozer android debug

# Build release APK
buildozer android release
```

### 5. Install on Device
```bash
# Enable USB debugging on Android device
# Connect via USB

# Install debug APK
adb install bin/apkfinder-1.0.0-debug.apk
```

## Common Commands

### Desktop Development
```bash
# Run app
python main.py

# Install dependencies
pip install -r requirements.txt

# Run with logging
python main.py --verbose
```

### Android Development
```bash
# Clean build
buildozer android clean

# Debug build
buildozer android debug

# Release build
buildozer android release

# Install and run
buildozer android debug install run

# View logs
buildozer android debug install run logcat
```

## Quick Configuration

### Server Settings
- URL: `http://your-server-ip:9301`
- Token: `cs` (default)
- Timeout: 30 seconds

### Download Settings
- Desktop: `~/Downloads/APK_Finder`
- Android: `/storage/emulated/0/Download/APK_Finder`

### ADB Settings
- Path: `adb` (if in PATH)
- Timeout: 60 seconds
- Flags: `-r -d -t`

## Troubleshooting

### Desktop Issues
```bash
# Missing dependencies
pip install kivy kivymd httpx

# Permission issues
chmod +x main.py

# Config issues
rm ~/.apk_finder/config.json
```

### Android Build Issues
```bash
# Missing Android SDK
export ANDROID_HOME=/opt/android-sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Build fails
buildozer android clean
buildozer android debug

# Permission denied
chmod +x ~/.buildozer/android/platform/android-sdk/tools/bin/sdkmanager
```

### Android Install Issues
```bash
# Enable unknown sources
# Settings → Security → Unknown sources

# USB debugging
# Settings → Developer options → USB debugging

# Install manually
adb install -r bin/apkfinder-1.0.0-debug.apk
```

## Next Steps

1. **Customize UI**: Edit `src/styles.py` for theming
2. **Add features**: Extend `src/main_window.py`
3. **Configure build**: Edit `buildozer.spec`
4. **Test thoroughly**: Test on different devices
5. **Deploy**: Build release APK for distribution

## Support

- Check full README.md for detailed documentation
- Review server logs for API issues
- Use `adb logcat` for Android debugging
- Check buildozer logs for build issues