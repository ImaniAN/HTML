import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import threading
import re
import logging
import json
import os
from datetime import datetime
import urllib3
import configparser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='cafe_client.log'
)

# Security Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.warning("SSL certificate verification is disabled. This is insecure in production.")

class ConfigManager:
    """Manages application configuration"""

    DEFAULT_CONFIG = {
        'Server': {
            'url': 'https://192.168.107.20:5000',
            'timeout': '10',
            'verify_ssl': 'False'
        },
        'Billing': {
            'rate_per_minute': '0.05',
            'currency': '$'
        },
        'UI': {
            'window_width': '400',
            'window_height': '350',
            'font_size': '12'
        }
    }

    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            self._create_default_config()

    def _create_default_config(self):
        """Create a default configuration file"""
        for section, options in self.DEFAULT_CONFIG.items():
            self.config[section] = options

        with open(self.config_file, 'w') as f:
            self.config.write(f)

        logging.info(f"Created default configuration file: {self.config_file}")

    def get(self, section, option, fallback=None):
        """Get configuration value with fallback"""
        return self.config.get(section, option, fallback=fallback)

    def get_float(self, section, option, fallback=None):
        """Get configuration value as float with fallback"""
        return self.config.getfloat(section, option, fallback=fallback)

    def get_int(self, section, option, fallback=None):
        """Get configuration value as integer with fallback"""
        return self.config.getint(section, option, fallback=fallback)

    def get_bool(self, section, option, fallback=None):
        """Get configuration value as boolean with fallback"""
        return self.config.getboolean(section, option, fallback=fallback)


class CafeClient:
    """Internet Cafe Client Application"""

    def __init__(self, root):
        """Initialize the cafe client application"""
        self.root = root
        self.config = ConfigManager()

        # Window setup
        self.root.title("Internet Cafe Client")
        width = self.config.get_int('UI', 'window_width', 400)
        height = self.config.get_int('UI', 'window_height', 350)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(400, 350)

        # Server configuration
        self.SERVER_URL = self.config.get('Server', 'url')
        self.TIMEOUT = self.config.get_int('Server', 'timeout', 10)
        self.VERIFY_SSL = self.config.get_bool('Server', 'verify_ssl', False)

        # Billing configuration
        self.RATE_PER_MINUTE = self.config.get_float('Billing', 'rate_per_minute', 0.05)
        self.CURRENCY = self.config.get('Billing', 'currency', '$')

        # Create a session to maintain cookies
        self.session = requests.Session()

        # Session state
        self.active_session = False
        self.session_start_time = None
        self.session_id = None
        self.logged_in = False
        self.update_timer_id = None

        # Threading lock
        self.request_lock = threading.Lock()

        # Create GUI elements
        self.setup_gui()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Test server connection on startup
        self.root.after(1000, self.test_server_connection)

        logging.info("Application initialized")

    def setup_gui(self):
        """Set up the GUI elements"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Internet Cafe Client",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)

        # Login frame
        login_frame = ttk.LabelFrame(main_frame, text="Authentication", padding="10")
        login_frame.pack(fill=tk.X, padx=5, pady=5)

        self.login_button = ttk.Button(
            login_frame,
            text="Login",
            command=self.login
        )
        self.login_button.pack(fill=tk.X, pady=5)

        # Session control frame
        session_frame = ttk.LabelFrame(main_frame, text="Session Control", padding="10")
        session_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_button = ttk.Button(
            session_frame,
            text="Start Session",
            command=self.start_session,
            state='disabled'
        )
        self.start_button.pack(fill=tk.X, pady=5)

        self.end_button = ttk.Button(
            session_frame,
            text="End Session",
            command=self.end_session,
            state='disabled'
        )
        self.end_button.pack(fill=tk.X, pady=5)

        # Session info frame
        info_frame = ttk.LabelFrame(main_frame, text="Session Information", padding="10")
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.time_label = ttk.Label(
            info_frame,
            text="Time: 0:00",
            font=("Arial", 12)
        )
        self.time_label.pack(pady=5)

        self.cost_label = ttk.Label(
            info_frame,
            text=f"Cost: {self.CURRENCY}0.00",
            font=("Arial", 12)
        )
        self.cost_label.pack(pady=5)

        # Progress indicator
        self.progress_var = tk.IntVar()
        self.progress = ttk.Progressbar(
            main_frame,
            mode="indeterminate",
            variable=self.progress_var
        )
        self.progress.pack(fill=tk.X, padx=5, pady=10)
        self.progress.pack_forget()  # Hidden by default

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def show_loading(self, show=True):
        """Show or hide loading indicator"""
        if show:
            self.progress.pack(fill=tk.X, padx=5, pady=10)
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress.pack_forget()

    def test_server_connection(self):
        """Test connection to the server"""
        self.status_var.set("Testing connection to server...")
        self.show_loading(True)

        # Run in a separate thread to avoid blocking UI
        threading.Thread(
            target=self._test_server_connection_thread,
            daemon=True
        ).start()

    def _test_server_connection_thread(self):
        """Test server connection in a background thread"""
        success = False
        try:
            with self.request_lock:
                response = self.session.get(
                    f'{self.SERVER_URL}/',
                    verify=self.VERIFY_SSL,
                    timeout=self.TIMEOUT
                )

            if response.status_code == 200:
                status_msg = "Server connection successful"
                success = True
            else:
                status_msg = f"Server returned status code: {response.status_code}"

                # Update UI from main thread
                self.root.after(0, lambda: messagebox.showwarning(
                    "Warning",
                    f"Server connection returned status code: {response.status_code}"
                ))

        except requests.exceptions.ConnectionError:
            status_msg = "Cannot connect to server"
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Cannot connect to server. Please check the server address and ensure the server is running."
            ))
        except requests.exceptions.Timeout:
            status_msg = "Connection timeout"
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Connection timed out. Server might be busy or unreachable."
            ))
        except Exception as e:
            status_msg = f"Connection error: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Connection error: {str(e)}"
            ))
            logging.error(f"Server connection error: {str(e)}")

        # Update UI from main thread
        self.root.after(0, lambda: self.status_var.set(status_msg))
        self.root.after(0, lambda: self.show_loading(False))

        logging.info(f"Server connection test: {status_msg}")
        return success

    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def login(self):
        """Handle login process"""
        email = simpledialog.askstring("Login", "Email:")
        if not email:
            return

        if not self.validate_email(email):
            messagebox.showerror("Error", "Invalid email format")
            return

        password = simpledialog.askstring("Login", "Password:", show="*")
        if not password:
            return

        self.status_var.set("Logging in...")
        self.show_loading(True)

        # Disable login button during login process
        self.login_button.config(state='disabled')

        # Run in a separate thread to avoid blocking UI
        threading.Thread(
            target=self._login_thread,
            args=(email, password),
            daemon=True
        ).start()

    def _login_thread(self, email, password):
        """Handle login in a background thread"""
        try:
            with self.request_lock:
                response = self.session.post(
                    f'{self.SERVER_URL}/login',
                    json={"email": email, "password": password},
                    verify=self.VERIFY_SSL,
                    timeout=self.TIMEOUT
                )

            if response.status_code == 200:
                self.logged_in = True

                # Update UI from main thread
                self.root.after(0, lambda: self.login_button.config(state='disabled'))
                self.root.after(0, lambda: self.start_button.config(state='normal'))
                self.root.after(0, lambda: self.status_var.set(f"Connected - Logged in as {email}"))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    "Logged in successfully"
                ))
            else:
                error_msg = "Unknown error"
                try:
                    error_msg = response.json().get('error', 'Unknown error')
                except ValueError:
                    error_msg = f"Invalid server response (Status: {response.status_code})"

                # Update UI from main thread
                self.root.after(0, lambda: self.status_var.set("Authentication failed"))
                self.root.after(0, lambda: self.login_button.config(state='normal'))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Login failed: {error_msg}"
                ))

        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.status_var.set("Connection failed"))
            self.root.after(0, lambda: self.login_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Cannot connect to server. Please check if the server is running."
            ))
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.status_var.set("Connection timeout"))
            self.root.after(0, lambda: self.login_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Connection timed out. Server might be busy or unreachable."
            ))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Connection error"))
            self.root.after(0, lambda: self.login_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Connection error: {str(e)}"
            ))
            logging.error(f"Login error: {str(e)}")

        # Hide loading indicator
        self.root.after(0, lambda: self.show_loading(False))

    def start_session(self):
        """Start a new session"""
        if not self.logged_in:
            messagebox.showerror("Error", "Please login first")
            return

        self.status_var.set("Starting session...")
        self.show_loading(True)

        # Disable start button during process
        self.start_button.config(state='disabled')

        # Run in a separate thread to avoid blocking UI
        threading.Thread(
            target=self._start_session_thread,
            daemon=True
        ).start()

    def _start_session_thread(self):
        """Handle session start in a background thread"""
        try:
            with self.request_lock:
                response = self.session.post(
                    f'{self.SERVER_URL}/start_session',
                    verify=self.VERIFY_SSL,
                    timeout=self.TIMEOUT
                )

            if response.status_code == 200:
                self.active_session = True
                self.session_start_time = datetime.now()

                # Safely get session ID
                try:
                    response_data = response.json()
                    self.session_id = response_data.get('session_id', 'unknown')
                except ValueError:
                    self.session_id = 'unknown'
                    logging.warning("Could not parse session ID from server response")

                # Update UI from main thread
                self.root.after(0, lambda: self.start_button.config(state='disabled'))
                self.root.after(0, lambda: self.end_button.config(state='normal'))
                self.root.after(0, lambda: self.status_var.set(
                    f"Session active - ID: {self.session_id}"
                ))

                # Start session timer
                self.root.after(0, self.update_session_info)

            elif response.status_code == 401:
                # Authentication issue
                self.logged_in = False

                # Update UI from main thread
                self.root.after(0, lambda: self.status_var.set("Not authenticated"))
                self.root.after(0, lambda: self.login_button.config(state='normal'))
                self.root.after(0, lambda: self.start_button.config(state='disabled'))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    "Not authenticated. Please login again."
                ))
            else:
                # Other error
                error_msg = "Unknown error"
                try:
                    error_msg = response.json().get('error', 'Unknown error')
                except ValueError:
                    error_msg = f"Invalid server response (Status: {response.status_code})"

                # Update UI from main thread
                self.root.after(0, lambda: self.status_var.set("Failed to start session"))
                self.root.after(0, lambda: self.start_button.config(state='normal'))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to start session: {error_msg}"
                ))

        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.status_var.set("Connection failed"))
            self.root.after(0, lambda: self.start_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Cannot connect to server. Please check if the server is running."
            ))
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.status_var.set("Connection timeout"))
            self.root.after(0, lambda: self.start_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Connection timed out. Server might be busy or unreachable."
            ))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Connection error"))
            self.root.after(0, lambda: self.start_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Connection error: {str(e)}"
            ))
            logging.error(f"Start session error: {str(e)}")

        # Hide loading indicator
        self.root.after(0, lambda: self.show_loading(False))

    def end_session(self):
        """End the current session"""
        self.status_var.set("Ending session...")
        self.show_loading(True)

        # Disable end button during process
        self.end_button.config(state='disabled')

        # Run in a separate thread to avoid blocking UI
        threading.Thread(
            target=self._end_session_thread,
            daemon=True
        ).start()

    def _end_session_thread(self):
        """Handle session end in a background thread"""
        try:
            with self.request_lock:
                response = self.session.post(
                    f'{self.SERVER_URL}/end_session',
                    verify=self.VERIFY_SSL,
                    timeout=self.TIMEOUT
                )

            if response.status_code == 200:
                self.active_session = False
                end_time = datetime.now()

                # Calculate session time and cost
                if self.session_start_time:
                    diff = end_time - self.session_start_time
                    minutes = diff.total_seconds() / 60
                    final_cost = minutes * self.RATE_PER_MINUTE

                    # Show session summary
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Session Ended",
                        f"Session time: {int(minutes)}:{int((minutes % 1) * 60):02d}\n"
                        f"Total cost: {self.CURRENCY}{final_cost:.2f}"
                    ))

                # Update UI from main thread
                self.root.after(0, lambda: self.start_button.config(state='normal'))
                self.root.after(0, lambda: self.end_button.config(state='disabled'))
                self.root.after(0, lambda: self.status_var.set("Session ended"))

                # Reset session state
                self.session_id = None
                self.session_start_time = None

                # Update session info UI
                self.root.after(0, self.update_session_info)

            elif response.status_code == 401:
                # Authentication issue
                self.logged_in = False
                self.active_session = False

                # Update UI from main thread
                self.root.after(0, lambda: self.status_var.set("Not authenticated"))
                self.root.after(0, lambda: self.login_button.config(state='normal'))
                self.root.after(0, lambda: self.start_button.config(state='disabled'))
                self.root.after(0, lambda: self.end_button.config(state='disabled'))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    "Not authenticated. Please login again."
                ))
            else:
                # Other error
                error_msg = "Unknown error"
                try:
                    error_msg = response.json().get('error', 'Unknown error')
                except ValueError:
                    error_msg = f"Invalid server response (Status: {response.status_code})"

                # Update UI from main thread
                self.root.after(0, lambda: self.status_var.set("Failed to end session"))
                self.root.after(0, lambda: self.end_button.config(state='normal'))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to end session: {error_msg}"
                ))

        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.status_var.set("Connection failed"))
            self.root.after(0, lambda: self.end_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Cannot connect to server. Please check if the server is running."
            ))
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.status_var.set("Connection timeout"))
            self.root.after(0, lambda: self.end_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "Connection timed out. Server might be busy or unreachable."
            ))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Connection error"))
            self.root.after(0, lambda: self.end_button.config(state='normal'))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Connection error: {str(e)}"
            ))
            logging.error(f"End session error: {str(e)}")

        # Hide loading indicator
        self.root.after(0, lambda: self.show_loading(False))

    def update_session_info(self):
        """Update the session information display"""
        # Cancel any existing update timer
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
            self.update_timer_id = None

        if self.active_session and self.session_start_time:
            # Calculate elapsed time
            now = datetime.now()
            diff = now - self.session_start_time
            minutes = diff.total_seconds() / 60

            # Update labels
            self.time_label.config(
                text=f"Time: {int(minutes)}:{int((minutes % 1) * 60):02d}"
            )
            self.cost_label.config(
                text=f"Cost: {self.CURRENCY}{minutes * self.RATE_PER_MINUTE:.2f}"
            )

            # Schedule next update
            self.update_timer_id = self.root.after(1000, self.update_session_info)
        else:
            # Reset labels
            self.time_label.config(text="Time: 0:00")
            self.cost_label.config(text=f"Cost: {self.CURRENCY}0.00")

    def on_closing(self):
        """Handle application closing"""
        if self.active_session:
            if messagebox.askyesno(
                "Confirm Exit",
                "You have an active session. End the session and exit?"
            ):
                # End the session first
                threading.Thread(
                    target=self._close_session_and_exit,
                    daemon=True
                ).start()
            else:
                return
        else:
            logging.info("Application shutting down")
            self.root.destroy()

    def _close_session_and_exit(self):
        """End current session and exit the application"""
        try:
            with self.request_lock:
                self.session.post(
                    f'{self.SERVER_URL}/end_session',
                    verify=self.VERIFY_SSL,
                    timeout=self.TIMEOUT
                )
        except Exception as e:
            logging.error(f"Error ending session on exit: {str(e)}")
        finally:
            logging.info("Application shutting down after session end")
            self.root.after(0, self.root.destroy)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CafeClient(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Unhandled exception: {str(e)}")
        messagebox.showerror(
            "Critical Error",
            f"An unexpected error occurred: {str(e)}\nSee log file for details."
        )