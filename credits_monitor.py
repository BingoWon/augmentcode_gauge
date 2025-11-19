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
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QProgressBar
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

        # Cookie storage file
        self.cookie_file = Path.home() / ".augment_credits_cookies.json"

        # Cookie storage
        self.cookies = {}
        self.cookie_expiry = None

        # Browser (background only)
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
        self.percentage_label = QLabel("--.-%")
        self.percentage_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.percentage_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.percentage_label)

        # Progress bar (thinner)
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
        """Setup the hidden browser for background cookie refresh."""
        # Create minimal browser for background cookie refresh only
        self.web_view = QWebEngineView()
        self.web_page = QWebEnginePage(QWebEngineProfile.defaultProfile(), self.web_view)
        self.web_view.setPage(self.web_page)

        # Connect cookie store
        cookie_store = self.web_page.profile().cookieStore()
        cookie_store.cookieAdded.connect(self.on_cookie_added)

        # Load existing cookies into browser
        self.load_cookies_into_browser()

    def load_cookies_into_browser(self):
        """Load saved cookies into the browser."""
        if not self.cookies:
            return

        from PySide6.QtNetwork import QNetworkCookie
        cookie_store = self.web_page.profile().cookieStore()

        for name, value in self.cookies.items():
            cookie = QNetworkCookie(name.encode(), value.encode())
            cookie.setDomain(".augmentcode.com")
            cookie.setPath("/")
            cookie_store.setCookie(cookie, QUrl("https://app.augmentcode.com"))

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
                            print(f"Cookies too old ({age_minutes:.1f} min), need fresh login")

            # No valid cookies found - need to login
            print("No saved cookies found. Please login via browser.")
            self.show_error_state()
            # Browser will auto-open on first API call failure

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
        """Setup timers for auto-refresh."""
        # Data refresh timer (every minute)
        self.data_refresh_timer = QTimer()
        self.data_refresh_timer.timeout.connect(self.fetch_credits)
        self.data_refresh_timer.start(self.data_refresh_interval)

        # Cookie refresh timer (every 50 minutes)
        self.cookie_refresh_timer = QTimer()
        self.cookie_refresh_timer.timeout.connect(self.refresh_cookies)
        self.cookie_refresh_timer.start(self.cookie_refresh_interval)

        # Initial fetch after 3 seconds (try existing cookies first)
        QTimer.singleShot(3000, self.fetch_credits)

    @Slot()
    def on_cookie_added(self, cookie):
        """Handle cookie added event."""
        cookie_name = cookie.name().data().decode()
        cookie_value = cookie.value().data().decode()

        # Don't overwrite _session cookie if it already has user info
        if cookie_name == '_session' and '_session' in self.cookies:
            # Check if existing cookie has user info
            import base64
            from urllib.parse import unquote
            try:
                existing_decoded = unquote(self.cookies['_session'])
                if '.' in existing_decoded:
                    payload = existing_decoded.split('.')[0]
                    decoded_payload = base64.b64decode(payload + '==').decode('utf-8', errors='ignore')
                    if 'userId' in decoded_payload:
                        # Existing cookie has user info, don't overwrite
                        return
            except:
                pass

        self.cookies[cookie_name] = cookie_value

        # Update cookie status and save
        if '_session' in self.cookies or 'web_rpc_proxy_session' in self.cookies:
            self.cookie_expiry = datetime.now() + timedelta(hours=1)
            # Save cookies immediately when updated
            self.save_cookies_to_file()





    @Slot()
    def refresh_cookies(self):
        """Automatically refresh cookies by reloading the page in background."""
        if self.web_view:
            self.web_view.setUrl(QUrl(self.login_url))
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
                print("Cookie expired. Please check saved cookies file.")
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.show_error_state()
            print(f"Error: {e}")

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
