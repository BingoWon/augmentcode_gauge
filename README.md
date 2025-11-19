# Augment Code Credits Monitor 📊

A simple GUI application with embedded browser to monitor your Augment Code API credits in real-time.

## Features ✨

- **Embedded Browser**: Built-in Chromium browser for easy login to Augment Code
- **Auto Cookie Management**: Automatically uses browser cookies for API authentication
- **Real-time Monitoring**: Displays your credits usage with auto-refresh every minute
- **Clean Interface**: Split-view design with browser on the left and metrics on the right
- **No Manual Cookie Copying**: Login once in the embedded browser, and the app handles the rest

## What It Displays 📈

- **Available Credits**: Total credits available
- **Used This Cycle**: Credits used in current billing cycle
- **Remaining Credits**: Credits remaining
- **Consumed Credits**: Total consumed in billing cycle
- **Last Update Time**: When data was last refreshed
- **Next Refresh Countdown**: Time until next automatic refresh

## Prerequisites 📋

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

## Installation 🚀

1. Clone or download this repository:
```bash
git clone <your-repo-url>
cd augmentcode_gauge
```

2. That's it! The `run.sh` script will handle dependencies automatically using `uv`.

## Usage 🎯

### Quick Start

Simply run the launch script:

```bash
./run.sh
```

Or run directly with uv:

```bash
uv run credits_monitor.py
```

### First Time Setup

1. **Launch the application** using `./run.sh`
2. **Login to Augment Code** in the embedded browser (left side)
   - The browser will open to `https://app.augmentcode.com/account/subscription`
   - Login with your credentials
3. **Click "Refresh Now"** button to fetch your credits data
4. **Done!** The app will now auto-refresh every minute

### Controls

- **🔄 Refresh Now**: Manually fetch latest credits data
- **🔄 Reload Page**: Reload the browser page
- **🗑️ Clear Cookies**: Clear all cookies (requires re-login)

## How It Works 🔧

1. The app embeds a full Chromium browser using PySide6's QWebEngineView
2. You login to Augment Code in this browser
3. The app uses JavaScript to fetch data from the API using the browser's cookies
4. Data is displayed in the right panel and refreshes automatically every 60 seconds
5. No need to manually copy cookies - everything is handled automatically!

## Project Structure 📁

```
augmentcode_gauge/
├── credits_monitor.py   # Main application code
├── pyproject.toml       # Project configuration and dependencies
├── run.sh              # Launch script
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Dependencies 📦

All dependencies are managed by `uv` and defined in `pyproject.toml`:

- **PySide6** (>=6.8.0): Qt for Python - provides GUI and embedded browser
- **requests** (>=2.31.0): HTTP library (for potential future enhancements)

## Troubleshooting 🔍

### "uv is not installed" error
Install uv using the command in the Prerequisites section.

### Browser shows blank page
Check your internet connection and try clicking "Reload Page".

### "Status: ✗ Failed" after clicking Refresh
Make sure you're logged in to Augment Code in the embedded browser first.

### Cookies not working
Try clicking "Clear Cookies" and login again.

## Technical Details 🛠️

- **Framework**: PySide6 (Qt for Python)
- **Browser Engine**: Chromium (via QWebEngineView)
- **Package Manager**: uv
- **Python Version**: 3.10+
- **API Endpoint**: `https://app.augmentcode.com/api/credits`

## Security Notes 🔒

- Cookies are stored in Qt's default profile location
- No cookies are sent to any third-party services
- All API calls are made directly from the embedded browser to Augment Code
- The app only accesses the Augment Code API

## License 📄

This is a personal utility tool. Use at your own discretion.

## Contributing 🤝

This is a simple personal tool, but feel free to fork and modify for your needs!

## Author ✍️

Created for monitoring Augment Code credits usage.

---

**Note**: This is an unofficial tool and is not affiliated with Augment Code.

