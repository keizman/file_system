# APK Finder Kivy Client

This is the Kivy-based client for APK Finder, designed to run on both desktop and Android platforms. It provides the same functionality as the PyQt5 Windows client but with cross-platform compatibility.

## Features

- **Cross-platform**: Runs on Windows, Linux, macOS, and Android
- **Modern UI**: Clean, responsive interface optimized for both desktop and mobile
- **Full functionality**: All features from the Windows client including:
  - Multi-server APK search
  - Build type filtering (Release/Debug/Combine)
  - File download with progress tracking
  - ADB integration for direct APK installation
  - Settings management
  - Connection status monitoring

## Requirements

### Desktop Development
- Python 3.8+
- Kivy 2.1.0+
- See `requirements.txt` for full list

### Android Development
- Linux environment (Ubuntu/Debian recommended)
- Buildozer
- Android SDK
- Java Development Kit (JDK)

## Installation

### Desktop Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

### Android Development Setup

1. Install buildozer:
```bash
pip install buildozer
```

2. Install Android development tools:
```bash
# Ubuntu/Debian
sudo apt install openjdk-8-jdk
sudo apt install android-sdk

# Set environment variables
export ANDROID_HOME=/usr/lib/android-sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

3. Initialize buildozer (first time only):
```bash
buildozer init
```

4. Build APK:
```bash
# Debug build
buildozer android debug

# Release build
buildozer android release
```

## Project Structure

```
kivy_client/
├── main.py                 # Main application entry point
├── buildozer.spec         # Android build configuration
├── requirements.txt       # Python dependencies
├── src/
│   ├── main_window.py     # Main UI screen
│   ├── settings_dialog.py # Settings popup
│   ├── styles.py          # UI styling and theming
│   ├── config.py          # Configuration management
│   ├── api_client.py      # HTTP API client
│   └── adb_manager.py     # Android Debug Bridge integration
├── shared/                # Shared utilities
│   ├── models.py          # Data models
│   └── utils.py           # Utility functions
└── resources/             # Application resources
    ├── icon.png           # App icon (512x512)
    └── presplash.png      # Splash screen (1280x720)
```

## Configuration

The app uses the same configuration system as the Windows client:

- **Desktop**: Config stored in `~/.apk_finder/config.json`
- **Android**: Config stored in app's private directory

### Default Settings

- Server URL: `http://localhost:9301`
- API Token: `cs`
- Download path: `~/Downloads/APK_Finder` (desktop) or app's downloads folder (Android)
- Theme: Light
- Build type: Release

## Usage

### Desktop Usage

1. **Launch the app**:
```bash
python main.py
```

2. **Configure server connection**:
   - Click "Settings" button
   - Go to "Server" tab
   - Enter server URL and API token
   - Click "Test Connection"

3. **Search for APKs**:
   - Select server and build type
   - Enter search keywords (use `|` for multiple keywords)
   - Click "Search"

4. **Download and install**:
   - Select file from results
   - Click "Download"
   - Connect Android device via USB
   - Click "Auto Install"

### Android Usage

1. **Install APK** on Android device
2. **Configure server connection** in Settings
3. **Search and download** APKs directly to device storage
4. **Install APKs** using system installer

## Android Deployment

### Prerequisites

- Linux development environment (WSL2 on Windows works)
- Android SDK and NDK
- JDK 8 or 11
- Buildozer

### Step-by-Step Build Process

1. **Prepare resources**:
```bash
# Create app icon (512x512 PNG)
cp /path/to/icon.png resources/icon.png

# Create splash screen (1280x720 PNG)
cp /path/to/splash.png resources/presplash.png
```

2. **Clean build** (if needed):
```bash
buildozer android clean
```

3. **Build debug APK**:
```bash
buildozer android debug
```

4. **Build release APK**:
```bash
buildozer android release
```

5. **Install on device**:
```bash
# Debug version
buildozer android debug install run

# Or manually install
adb install bin/apkfinder-1.0.0-debug.apk
```

### Build Configuration

Edit `buildozer.spec` for customization:

- **App details**: title, package name, version
- **Permissions**: Internet, storage access
- **Architecture**: ARM64, ARMv7
- **Python requirements**: All dependencies listed
- **Android API**: Target SDK version

### Common Build Issues

1. **Missing dependencies**:
```bash
# Install missing system packages
sudo apt install python3-pip python3-dev python3-venv
sudo apt install libffi-dev libssl-dev build-essential
```

2. **Android SDK issues**:
```bash
# Download Android SDK command line tools
# Set ANDROID_HOME environment variable
export ANDROID_HOME=/opt/android-sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

3. **NDK issues**:
```bash
# Buildozer will download NDK automatically
# Or specify custom NDK path in buildozer.spec
```

## Performance Considerations

### Desktop Performance
- Efficient table rendering for large file lists
- Async API calls to prevent UI freezing
- Threaded downloads with progress callbacks

### Android Performance
- Optimized layouts for touch interfaces
- Efficient memory usage for mobile devices
- Background processing for downloads

## Differences from Windows Client

### UI Differences
- **Touch-friendly**: Larger buttons and touch targets
- **Responsive layout**: Adapts to different screen sizes
- **Mobile navigation**: Simplified menu structure

### Platform-Specific Features
- **Android storage**: Uses Android's scoped storage
- **System integration**: Uses Android's file picker and installer
- **Network permissions**: Requires explicit permission on Android

### Removed Features
- **System tray**: Not available on mobile
- **Window management**: Mobile apps are fullscreen
- **Desktop notifications**: Uses Android notifications instead

## Development Tips

### Testing on Desktop
- Use desktop mode for rapid development
- Test responsive layouts by resizing window
- Use debug logging for troubleshooting

### Testing on Android
- Use `buildozer android debug` for quick builds
- Enable USB debugging on device
- Use `adb logcat` for debugging

### Code Structure
- Keep UI logic in screen classes
- Use threading for blocking operations
- Implement proper error handling
- Follow Kivy conventions for widget creation

## Troubleshooting

### Common Issues

1. **Import errors**:
   - Check Python path configuration
   - Verify all dependencies are installed
   - Check for circular imports

2. **UI not responsive**:
   - Ensure UI updates happen on main thread
   - Use Clock.schedule_once for threading callbacks
   - Avoid blocking operations in UI thread

3. **Build failures**:
   - Check buildozer.spec configuration
   - Verify Android SDK installation
   - Clean build directory and retry

4. **APK installation fails**:
   - Check Android device permissions
   - Enable "Unknown sources" in Android settings
   - Verify APK signature

### Debug Commands

```bash
# View build logs
buildozer android debug -v

# Clear cache
buildozer android clean

# Check dependencies
buildozer android requirements

# Run on device with logs
buildozer android debug install run logcat
```

## Contributing

1. Follow Python coding standards
2. Test on both desktop and Android
3. Update documentation for new features
4. Use meaningful commit messages

## License

Same as the main APK Finder project.