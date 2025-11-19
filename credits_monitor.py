#!/usr/bin/env python3
"""
Augment Code Credits Monitor
A fully automated GUI application that monitors Augment Code API credits.
Features automatic cookie refresh to maintain persistent login.
"""

import sys
import json
import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QGroupBox, QInputDialog, QTextEdit, QDialog, QDialogButtonBox
)
from PySide6.QtCore import QTimer, Qt, QUrl, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile


class CreditsMonitor(QMainWindow):
    """Main application window with automatic cookie management."""

    def __init__(self):
        super().__init__()
        self.api_url = "https://app.augmentcode.com/api/credits"
        self.login_url = "https://app.augmentcode.com/account/subscription"
        self.data_refresh_interval = 60000  # 60 seconds - API call frequency
        self.cookie_refresh_interval = 50 * 60 * 1000  # 50 minutes - cookie refresh
        self.countdown_seconds = 60
        self.cookie_countdown_seconds = 50 * 60

        # Cookie storage file
        self.cookie_file = Path.home() / ".augment_credits_cookies.json"

        # Cookie storage
        self.cookies = {}
        self.cookie_expiry = None

        # Browser (hidden by default)
        self.browser_widget = None
        self.web_view = None
        self.web_page = None

        self.init_ui()
        self.setup_browser()
        self.load_cookies_from_file()
        self.setup_timers()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Credits")
        self.setGeometry(100, 100, 220, 85)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 8, 10, 8)

        # Percentage (large and prominent)
        self.percentage_label = QLabel("--.-%)")
        self.percentage_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.percentage_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.percentage_label)

        # Progress bar (thinner)
        from PySide6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1000)  # Use 1000 for decimal precision
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { height: 14px; }")
        main_layout.addWidget(self.progress_bar)

        # Credits numbers (remaining / total)
        self.credits_label = QLabel("--- / ---")
        self.credits_label.setStyleSheet("font-size: 12px;")
        self.credits_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.credits_label)

    def setup_browser(self):
        """Setup the hidden browser for cookie management."""
        self.browser_widget = QWidget()
        layout = QVBoxLayout(self.browser_widget)

        # Browser controls
        controls_layout = QHBoxLayout()

        url_label = QLabel(f"🌐 {self.login_url}")
        url_label.setStyleSheet("font-weight: bold; padding: 5px;")
        controls_layout.addWidget(url_label)

        controls_layout.addStretch()

        reload_btn = QPushButton("🔄 Reload")
        reload_btn.clicked.connect(self.reload_browser)
        controls_layout.addWidget(reload_btn)

        hide_btn = QPushButton("✓ Done (Hide Browser)")
        hide_btn.clicked.connect(self.hide_browser)
        controls_layout.addWidget(hide_btn)

        layout.addLayout(controls_layout)

        # Web view
        self.web_view = QWebEngineView()
        self.web_page = QWebEnginePage(QWebEngineProfile.defaultProfile(), self.web_view)
        self.web_view.setPage(self.web_page)

        # Connect cookie store
        cookie_store = self.web_page.profile().cookieStore()
        cookie_store.cookieAdded.connect(self.on_cookie_added)

        layout.addWidget(self.web_view)

        # Info label
        info_label = QLabel(
            "💡 Login to Augment Code above. Click 'Done' when finished. "
            "The app will automatically refresh cookies every 50 minutes."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "padding: 10px; border: 1px solid palette(mid); "
            "border-radius: 5px;"
        )
        layout.addWidget(info_label)

        self.browser_widget.setWindowTitle("Augment Code Login")
        self.browser_widget.resize(1000, 700)




    def load_cookies_from_file(self):
        """Load cookies from file, or use initial cookies if file doesn't exist."""
        try:
            if self.cookie_file.exists():
                # Load from file
                with open(self.cookie_file, 'r') as f:
                    data = json.load(f)
                    self.cookies = data.get('cookies', {})

                    # Check if cookies are still valid (within 55 minutes)
                    saved_time = data.get('saved_at')
                    if saved_time:
                        saved_datetime = datetime.fromisoformat(saved_time)
                        age_minutes = (datetime.now() - saved_datetime).total_seconds() / 60

                        if age_minutes < 55:  # Still fresh
                            self.cookie_expiry = saved_datetime + timedelta(hours=1)
                            print(f"Loaded cookies from file (age: {age_minutes:.1f} min)")
                            return
                        else:
                            print(f"Cookies too old ({age_minutes:.1f} min), using initial cookies")

            # Fallback to initial cookies
            initial_cookies = {
                'ph_phc_TXdpocbGVeZVm5VJmAsHTMrCofBQu3e0kN8HGMNGTVW_posthog': '%7B%22distinct_id%22%3A%22019726d0-7c6c-76c5-831b-8a62820cac48%22%2C%22%24sesid%22%3A%5B1757501448384%2C%220199333f-e0a1-7afe-8bce-3f2ad90ba5a2%22%2C1757501448353%5D%7D',
                'ajs_user_id': 'fcacaa74-0118-496f-8432-5a2b74d79dfc',
                '_session': 'eyJvYXV0aDI6c3RhdGUiOiJpU1NiQm1RWFZpdHZZQmhHQWhEdklXaFRVdmRTMjZESjZrRmZuY1JFQlBRIiwib2F1dGgyOmNvZGVWZXJpZmllciI6IlBvbzdhQzVsQ2FQX1JxdktZTnVZU051cFR1eXI5eEtnZmR3anlQbDBUeFkiLCJ1c2VyIjp7InVzZXJJZCI6ImZjYWNhYTc0LTAxMTgtNDk2Zi04NDMyLTVhMmI3NGQ3OWRmYyIsInRlbmFudElkIjoiNGRkZDgzYWVlODdiNzZlNGE3M2JmODNlZWQ3MzBmMmYiLCJ0ZW5hbnROYW1lIjoiZDExLWRpc2NvdmVyeTYiLCJzaGFyZE5hbWVzcGFjZSI6ImQxMSIsImVtYWlsIjoiQmluZ293QG91dGxvb2suY29tIiwicm9sZXMiOltdLCJjcmVhdGVkQXQiOjE3NjM1NTcxMDIzNzQsInNlc3Npb25JZCI6ImI2NzM0OGY4LWMwYTItNGUzOS04MTlhLThlNDMwOTg4YjYxZSJ9fQ%3D%3D.m5khOjUrFY%2Fxb0Isz9X59NJH1irkJefTiO5mkFWCAPU',
                'web_rpc_proxy_session': 'MTc2MzU1NzE5NHxYelNuOWdha1p4WHpnNFc4RTd3VngzZ3ZqVlhXNHVKdXlrbzJoOUJCOEVzdXB0ZTNsMFZMMHVCREtuWXpKS2RLdWlGb0MxUWVKZHRlaFFxSUNqcW42NVlyWFNjaEcxNVpqTVZEamZUVUZnT3NuM3RoMnJVMmdhcklsTnVGVFhpcEE3T3pFbnEzOXRXTUY4V1MzQU84Vy1ubGJvdzBpeFRNczNoX3JNT3lQLTBJNzdPS2xJX3NvNmRxZDhCYzNzUWR0WTg5REtzWkRNV2k0RVVaSWh5MzN5dWpQc1NSLXhVPXy-cqQUoQTWtiJ-sqRJbLHizLsA0RrY_s2sUtGPgIwkxA=='
            }
            self.cookies.update(initial_cookies)
            self.cookie_expiry = datetime.now() + timedelta(hours=1)
            print("Using initial cookies")

        except Exception as e:
            print(f"Error loading cookies: {e}")
            self.show_error_state()

    def save_cookies_to_file(self):
        """Save current cookies to file."""
        try:
            data = {
                'cookies': self.cookies,
                'saved_at': datetime.now().isoformat()
            }
            with open(self.cookie_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved cookies to {self.cookie_file}")
        except Exception as e:
            print(f"Error saving cookies: {e}")

    def setup_timers(self):
        """Setup timers for auto-refresh and countdown."""
        # Data refresh timer (every minute)
        self.data_refresh_timer = QTimer()
        self.data_refresh_timer.timeout.connect(self.fetch_credits)
        self.data_refresh_timer.start(self.data_refresh_interval)

        # Cookie refresh timer (every 50 minutes)
        self.cookie_refresh_timer = QTimer()
        self.cookie_refresh_timer.timeout.connect(self.refresh_cookies)
        self.cookie_refresh_timer.start(self.cookie_refresh_interval)

        # Countdown timer (updates every second)
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

        # Initial fetch after 3 seconds (give time for cookies to load)
        QTimer.singleShot(3000, self.fetch_credits)

    @Slot()
    def on_cookie_added(self, cookie):
        """Handle cookie added event."""
        cookie_name = cookie.name().data().decode()
        cookie_value = cookie.value().data().decode()
        self.cookies[cookie_name] = cookie_value

        # Update cookie status and save
        if '_session' in self.cookies or 'web_rpc_proxy_session' in self.cookies:
            self.cookie_expiry = datetime.now() + timedelta(hours=1)
            # Save cookies immediately when updated
            self.save_cookies_to_file()

    @Slot()
    def show_browser(self):
        """Show the browser window for login."""
        if not self.browser_widget:
            self.setup_browser()

        self.web_view.setUrl(QUrl(self.login_url))
        self.browser_widget.show()

    @Slot()
    def hide_browser(self):
        """Hide the browser window."""
        if self.browser_widget:
            self.browser_widget.hide()

    @Slot()
    def reload_browser(self):
        """Reload the browser page."""
        if self.web_view:
            self.web_view.reload()

    @Slot()
    def import_cookies_dialog(self):
        """Show dialog to import cookies from clipboard."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Cookies")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        # Instructions
        instructions = QLabel(
            "<b>Paste your cookies here:</b><br>"
            "Format: name1=value1; name2=value2; ...<br>"
            "Or one cookie per line: name=value"
        )
        layout.addWidget(instructions)

        # Text edit for cookies
        text_edit = QTextEdit()
        text_edit.setPlaceholderText(
            "Example:\n"
            "_session=abc123; web_rpc_proxy_session=xyz789\n\n"
            "Or:\n"
            "_session=abc123\n"
            "web_rpc_proxy_session=xyz789"
        )
        layout.addWidget(text_edit)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.Accepted:
            cookie_text = text_edit.toPlainText().strip()
            if cookie_text:
                self.parse_and_load_cookies(cookie_text)

    def parse_and_load_cookies(self, cookie_text):
        """Parse cookie text and load into storage."""
        try:
            new_cookies = {}

            # Try parsing as semicolon-separated (browser format)
            if ';' in cookie_text:
                pairs = cookie_text.split(';')
                for pair in pairs:
                    pair = pair.strip()
                    if '=' in pair:
                        name, value = pair.split('=', 1)
                        new_cookies[name.strip()] = value.strip()
            else:
                # Try parsing as line-separated
                lines = cookie_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if '=' in line:
                        name, value = line.split('=', 1)
                        new_cookies[name.strip()] = value.strip()

            if new_cookies:
                self.cookies.update(new_cookies)
                self.cookie_expiry = datetime.now() + timedelta(hours=1)
                # Save imported cookies
                self.save_cookies_to_file()
                QTimer.singleShot(1000, self.fetch_credits)
            else:
                raise ValueError("No valid cookies")

        except Exception as e:
            self.show_error_state()
            print(f"Import error: {e}")

    @Slot()
    def refresh_cookies(self):
        """Automatically refresh cookies by reloading the page in background."""
        if self.web_view:
            self.web_view.setUrl(QUrl(self.login_url))
            self.cookie_countdown_seconds = 50 * 60
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-refreshing cookies...")
            # Cookies will be saved automatically via on_cookie_added callback

    @Slot()
    def fetch_credits(self):
        """Fetch credits data from API using stored cookies."""
        if not self.cookies:
            self.show_error_state()
            return

        try:
            response = requests.get(
                self.api_url,
                cookies=self.cookies,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.handle_credits_response(data)
            elif response.status_code == 401 or response.status_code == 403:
                self.show_error_state()
                self.show_browser()
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.show_error_state()
            print(f"Error: {e}")

        self.countdown_seconds = 60

    def handle_credits_response(self, data):
        """Handle the response from credits API (called after successful fetch)."""
        try:
            self.update_credits_display(data)
        except Exception as e:
            self.show_error_state()
            print(f"Error: {e}")

    def update_credits_display(self, data):
        """Update the credits display with new data."""
        remaining = data.get("usageUnitsRemaining", 0)
        total = remaining + data.get("usageUnitsConsumedThisBillingCycle", 0)

        # Calculate percentage with one decimal place
        if total > 0:
            percentage = (remaining / total) * 100
            percentage_int = int(percentage * 10)  # For progress bar (0-1000)
            self.progress_bar.setValue(percentage_int)
        else:
            percentage = 0.0
            self.progress_bar.setValue(0)

        # Update labels - reset to normal style
        self.percentage_label.setText(f"{percentage:.1f}%")
        self.percentage_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.credits_label.setText(f"{remaining:,} / {total:,}")
        self.credits_label.setStyleSheet("font-size: 12px;")
        self.progress_bar.setStyleSheet("QProgressBar { height: 14px; }")

    def show_error_state(self):
        """Show error state with red styling."""
        self.percentage_label.setText("ERROR")
        self.percentage_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f44336;")
        self.credits_label.setText("--- / ---")
        self.credits_label.setStyleSheet("font-size: 12px; color: #f44336;")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { height: 14px; } QProgressBar::chunk { background-color: #f44336; }")

    @Slot()
    def update_countdown(self):
        """Update the countdown timer display."""
        self.countdown_seconds -= 1
        if self.countdown_seconds < 0:
            self.countdown_seconds = 60

        self.cookie_countdown_seconds -= 1
        if self.cookie_countdown_seconds < 0:
            self.cookie_countdown_seconds = 50 * 60


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Augment Code Credits Monitor")
    app.setOrganizationName("AugmentCode")

    # Create and show main window
    window = CreditsMonitor()
    window.show()

    # Save cookies on exit
    app.aboutToQuit.connect(window.save_cookies_to_file)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
