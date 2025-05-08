import tkinter as tk from tkinter import ttk, messagebox, simpledialog 
import requests from datetime import datetime import urllib3

# Disable InsecureRequestWarning for development purposes
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CafeClient:
    def __init__(self, root):
    
        self.root = root
        self.root.title("Internet Cafe Client")
        self.root.geometry("400x350")  # Set window size
        
        # Configuration
        self.SERVER_URL = 'https://192.168.107.20:5000'  
        
        # Create a session to maintain cookies
        self.session = requests.Session()
        
        # Session variables
        self.active_session = False
        self.session_start_time = None
        self.session_id = None
        self.logged_in = False
        
        # Create GUI elements
        self.setup_gui()
        
        # Test server connection on startup
        self.root.after(1000, self.test_server_connection)
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Internet Cafe Client", font=("Arial", 16, "bold"))
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
        
        self.time_label = ttk.Label(info_frame, text="Time: 0:00", font=("Arial", 12))
        self.time_label.pack(pady=5)
        
        self.cost_label = ttk.Label(info_frame, text="Cost: $0.00", font=("Arial", 12))
        self.cost_label.pack(pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Connecting to server...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def test_server_connection(self):
        try:
            self.status_var.set("Testing connection to server...")
            self.root.update()
            
            response = self.session.get(
                f'{self.SERVER_URL}/',
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                self.status_var.set("Server connection successful")
                return True
            else:
                self.status_var.set(f"Server returned status code: {response.status_code}")
                messagebox.showwarning("Warning", f"Server connection returned status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.status_var.set("Cannot connect to server")
            messagebox.showerror("Error", "Cannot connect to server. Please check the server address and ensure the server is running.")
            return False
        except requests.exceptions.Timeout:
            self.status_var.set("Connection timeout")
            messagebox.showerror("Error", "Connection timed out. Server might be busy or unreachable.")
            return False
        except requests.exceptions.RequestException as e:
            self.status_var.set("Connection error")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
            return False
    
    def login(self):
        email = simpledialog.askstring("Login", "Email:")
        if not email:
            return
            
        password = simpledialog.askstring("Login", "Password:", show="*")
        if not password:
            return
            
        try:
            self.status_var.set("Connecting to server...")
            self.root.update()
            
            response = self.session.post(
                f'{self.SERVER_URL}/login',
                json={"email": email, "password": password},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logged_in = True
                self.login_button.config(state='disabled')
                self.start_button.config(state='normal')
                self.status_var.set("Connected - Logged in as " + email)
                messagebox.showinfo("Success", "Logged in successfully")
            else:
                error_msg = response.json().get('error', 'Unknown error')
                self.status_var.set("Authentication failed")
                messagebox.showerror("Error", f"Login failed: {error_msg}")
                
        except requests.exceptions.ConnectionError:
            self.status_var.set("Connection failed")
            messagebox.showerror("Error", "Cannot connect to server. Please check if the server is running.")
        except requests.exceptions.Timeout:
            self.status_var.set("Connection timeout")
            messagebox.showerror("Error", "Connection timed out. Server might be busy or unreachable.")
        except requests.exceptions.RequestException as e:
            self.status_var.set("Connection error")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def start_session(self):
        if not self.logged_in:
            messagebox.showerror("Error", "Please login first")
            return
            
        try:
            self.status_var.set("Starting session...")
            self.root.update()
            
            response = self.session.post(
                f'{self.SERVER_URL}/start_session',
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                self.active_session = True
                self.session_start_time = datetime.now()
                self.session_id = response.json().get('session_id', 'unknown')
                
                self.start_button.config(state='disabled')
                self.end_button.config(state='normal')
                self.status_var.set(f"Session active - ID: {self.session_id}")
                self.update_session_info()
            elif response.status_code == 401:
                self.status_var.set("Not authenticated")
                messagebox.showerror("Error", "Not authenticated. Please login again.")
                self.logged_in = False
                self.login_button.config(state='normal')
                self.start_button.config(state='disabled')
            else:
                error_msg = response.json().get('error', 'Unknown error')
                self.status_var.set("Failed to start session")
                messagebox.showerror("Error", f"Failed to start session: {error_msg}")
                
        except requests.exceptions.ConnectionError:
            self.status_var.set("Connection failed")
            messagebox.showerror("Error", "Cannot connect to server. Please check if the server is running.")
        except requests.exceptions.Timeout:
            self.status_var.set("Connection timeout")
            messagebox.showerror("Error", "Connection timed out. Server might be busy or unreachable.")
        except requests.exceptions.RequestException as e:
            self.status_var.set("Connection error")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def end_session(self):
        try:
            self.status_var.set("Ending session...")
            self.root.update()
            
            response = self.session.post(
                f'{self.SERVER_URL}/end_session',
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                self.active_session = False
                end_time = datetime.now()
                
                if self.session_start_time:
                    diff = end_time - self.session_start_time
                    minutes = diff.total_seconds() / 60
                    final_cost = minutes * 0.05  # $0.05 per minute
                    messagebox.showinfo("Session Ended", 
                                        f"Session time: {int(minutes)}:{int((minutes % 1) * 60):02d}\n"
                                        f"Total cost: ${final_cost:.2f}")
                
                self.start_button.config(state='normal')
                self.end_button.config(state='disabled')
                self.status_var.set("Session ended")
                self.update_session_info()
            elif response.status_code == 401:
                self.status_var.set("Not authenticated")
                messagebox.showerror("Error", "Not authenticated. Please login again.")
                self.logged_in = False
                self.login_button.config(state='normal')
                self.start_button.config(state='disabled')
                self.end_button.config(state='disabled')
            else:
                error_msg = response.json().get('error', 'Unknown error')
                self.status_var.set("Failed to end session")
                messagebox.showerror("Error", f"Failed to end session: {error_msg}")
                
        except requests.exceptions.ConnectionError:
            self.status_var.set("Connection failed")
            messagebox.showerror("Error", "Cannot connect to server. Please check if the server is running.")
        except requests.exceptions.Timeout:
            self.status_var.set("Connection timeout")
            messagebox.showerror("Error", "Connection timed out. Server might be busy or unreachable.")
        except requests.exceptions.RequestException as e:
            self.status_var.set("Connection error")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def update_session_info(self):
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
                text=f"Cost: ${minutes * 0.05:.2f}"  # $0.05 per minute
            )
            
            # Schedule next update
            self.root.after(1000, self.update_session_info)
        else:
            # Reset labels
            self.time_label.config(text="Time: 0:00")
            self.cost_label.config(text="Cost: $0.00")

if __name__ == "__main__":
    root = tk.Tk()
    app = CafeClient(root)
    root.mainloop()
