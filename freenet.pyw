import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import base64
import urllib.parse
from urllib.parse import urlparse, parse_qs
import subprocess
import os
import time
import requests
import socket
import random
import concurrent.futures
from tqdm import tqdm
import threading
import queue
import sys
from datetime import datetime
import winreg
import qrcode
from PIL import ImageTk, Image
if sys.platform == 'win32':
    from subprocess import CREATE_NO_WINDOW



def kill_xray_processes():
        """Kill any existing Xray processes"""
        try:
            if sys.platform == 'win32':
                # Windows implementation
                import psutil
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'] == 'xray.exe':
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                # Linux/macOS implementation
                import signal
                import subprocess
                subprocess.run(['pkill', '-f', 'xray'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            #self.log(f"Error killing existing Xray processes: {str(e)}")
            pass


class VPNConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN Config Manager")
        self.root.geometry("600x700+620+20") # Increased height for new panel
        
        # Configure dark theme
        self.setup_dark_theme()
        
        # --- Initialize Logging Queues ---
        # This must be done before any method that might call self.log()
        self.log_queue = queue.Queue()
        self.xray_log_queue = queue.Queue()
        
        # Kill any existing Xray processes
        self.kill_existing_xray_processes()

        self.stop_event = threading.Event()
        self.thread_lock = threading.Lock()
        self.active_threads = []
        self.is_fetching = False
        
        # --- UI and Logging Setup ---
        # Create all UI elements first, then set up the logging systems that use them.
        self.setup_ui()
        self.setup_logging()
        self.setup_xray_logging()

        # --- Configuration ---
        # Now it's safe to call methods that might log messages.
        self.load_mirrors()
        
        # Set a default mirror URL.
        if self.MIRRORS:
            default_mirror_key = next(iter(self.MIRRORS))
            self.CONFIGS_URL = self.MIRRORS[default_mirror_key]
        else:
            self.log("CRITICAL: No mirrors loaded. Please create a valid 'sub.txt'.")
            self.CONFIGS_URL = ""

        self.WORKING_CONFIGS_FILE = "working_configs.txt"
        self.BEST_CONFIGS_FILE = "best_configs.txt"
        
        self.TEMP_FOLDER = os.path.join(os.getcwd(), "temp")
        self.TEMP_CONFIG_FILE = os.path.join(self.TEMP_FOLDER, "temp_config.json")
        self.XRAY_PATH = os.path.join(os.getcwd(), "xray.exe")
        self.TEST_TIMEOUT = 10
        self.SOCKS_PORT = 1080
        self.PING_TEST_URL = "https://old-queen-f906.mynameissajjad.workers.dev/login"
        self.LATENCY_WORKERS = 100
        
        if not os.path.exists(self.TEMP_FOLDER):
            os.makedirs(self.TEMP_FOLDER)
        
        # --- Variable Initialization ---
        self.best_configs = []
        self.selected_config = None
        self.connected_config = None
        self.xray_process = None
        self.is_connected = False
        self.total_configs = 0
        self.tested_configs = 0
        self.working_configs = 0
        
        # Load best configs if file exists
        if os.path.exists(self.BEST_CONFIGS_FILE):
            self.load_best_configs()
            
    def load_mirrors(self):
        """Loads subscription mirrors from sub.txt."""
        self.MIRRORS = {}
        subs_file = "sub.txt"
        
        fallback_mirrors = {
            "barry-far": "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
            "SoliSpirit": "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt",
        }

        if not os.path.exists(subs_file):
            self.log(f"'{subs_file}' not found. Using default mirrors.")
            self.MIRRORS = fallback_mirrors
            return

        try:
            with open(subs_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            if not lines:
                self.log(f"'{subs_file}' is empty. Using default mirrors.")
                self.MIRRORS = fallback_mirrors
                return

            json_content = "{\n" + ",\n".join(lines) + "\n}"
            self.MIRRORS = json.loads(json_content)
            self.log(f"Successfully loaded {len(self.MIRRORS)} mirrors from {subs_file}.")

        except json.JSONDecodeError as e:
            self.log(f"Error decoding JSON from '{subs_file}': {e}. Using default mirrors.")
            self.MIRRORS = fallback_mirrors
        except Exception as e:
            self.log(f"An unexpected error occurred while loading mirrors: {e}. Using default mirrors.")
            self.MIRRORS = fallback_mirrors

    def setup_dark_theme(self):
        """Configure dark theme colors"""
        self.root.tk_setPalette(background='#2d2d2d', foreground='#ffffff',
                                 activeBackground='#3e3e3e', activeForeground='#ffffff')

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background='#2d2d2d', foreground='#ffffff')
        style.configure('TFrame', background='#2d2d2d')
        style.configure('TLabel', background='#2d2d2d', foreground='#ffffff')
        style.configure('TEntry', fieldbackground='#3e3e3e', foreground='#ffffff')
        style.configure('TScrollbar', background='#3e3e3e')
        
        style.configure('Treeview', 
                        background='#3e3e3e', 
                        foreground='#ffffff', 
                        fieldbackground='#3e3e3e')
        style.configure('Treeview.Heading', 
                        background='#3e3e3e', 
                        foreground='#ffffff')
        
        style.map('Treeview.Heading', 
                  background=[('active', '#3e3e3e')],
                  foreground=[('active', '#ffffff')])
        
        style.map('Treeview', background=[('selected', '#4a6984')])
        style.configure('Vertical.TScrollbar', background='#3e3e3e')
        style.configure('Horizontal.TScrollbar', background='#3e3e3e')
        style.configure('TProgressbar', background='#4a6984', troughcolor='#3e3e3e')

        style.configure('TButton', 
                        background='#3e3e3e', 
                        foreground='#ffffff', 
                        relief='flat',
                        focuscolor='#3e3e3e',
                        focusthickness=0)
        
        style.map('TButton',
                  background=[('!active', '#3e3e3e'), ('pressed', '#3e3e3e')],
                  foreground=[('disabled', '#888888')])
        
        style.configure('Stop.TButton', 
                        background='Tomato', 
                        foreground='#ffffff',
                        focuscolor='Tomato',
                        focusthickness=0)
        
        style.map('Stop.TButton',
                  background=[('!active', 'Tomato'), ('pressed', 'Tomato')],
                  foreground=[('disabled', '#888888')])
        
    def setup_ui(self):
        # --- Top Fixed Frame ---
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, pady=(10, 5), padx=10)

        # Buttons      
        self.fetch_btn = ttk.Button(top_frame, text="Fetch & Test New Configs", command=self.fetch_and_test_configs, cursor='hand2')
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.connect_btn = ttk.Button(top_frame, text="Connect", command=self.connect_config, state=tk.DISABLED, cursor='hand2')
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(top_frame, text="Disconnect", command=self.click_disconnect_config_button, state=tk.DISABLED, cursor='hand2')
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.reload_btn = ttk.Button(top_frame, text="Reload Best Configs", command=self.reload_and_test_configs, cursor='hand2')
        self.reload_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_label = ttk.Label(top_frame, text="Disconnected", foreground="Tomato")
        self.status_label.pack(side=tk.RIGHT)

        # --- Main Paned Window ---
        main_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashwidth=8, bg="#2d2d2d")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- Middle Treeview Frame (Top Pane) ---
        self.middle_frame = ttk.Frame(main_pane)
        columns = ('Index', 'Latency', 'Protocol', 'Server', 'Port' ,'Config')
        self.tree = ttk.Treeview(self.middle_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center', minwidth=50)
        self.tree.column('Index', width=50, minwidth=50)
        self.tree.column('Latency', width=100, minwidth=80)
        self.tree.column('Protocol', width=80, minwidth=80)
        self.tree.column('Server', width=150, minwidth=150)
        self.tree.column('Port', width=80, minwidth=80)
        self.tree.column('Config', width=400, anchor='w', minwidth=150)
        tree_vscrollbar = ttk.Scrollbar(self.middle_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_vscrollbar.set)
        tree_hscrollbar = ttk.Scrollbar(self.middle_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=tree_hscrollbar.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_vscrollbar.grid(row=0, column=1, sticky='ns')
        tree_hscrollbar.grid(row=1, column=0, sticky='ew')
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure('connected', background='#2d5a2d', foreground='#90EE90')
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind('<Double-1>', self.on_config_select)
        self.root.bind('<Control-v>', self.paste_configs)
        self.root.bind('<Control-c>', self.copy_selected_configs)
        self.root.bind('<Delete>', self.delete_selected_configs)
        self.root.bind('<q>', self.generate_qrcode)
        self.root.bind('<Q>', self.generate_qrcode)
        main_pane.add(self.middle_frame)

        # --- Bottom Frame Container (Bottom Pane) ---
        bottom_frame_container = ttk.Frame(main_pane)
        main_pane.add(bottom_frame_container)

        # --- General Logs Frame (inside bottom container) ---
        log_frame = ttk.LabelFrame(bottom_frame_container, text="Logs")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 5))
        counter_frame = ttk.Frame(log_frame)
        counter_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        self.tested_label = ttk.Label(counter_frame, text="Tested: 0")
        self.tested_label.pack(side=tk.LEFT, padx=(0, 10))
        self.total_label = ttk.Label(counter_frame, text="Total: 0")
        self.total_label.pack(side=tk.LEFT)
        self.working_label = ttk.Label(counter_frame, text="Working: 0")
        self.working_label.pack(side=tk.LEFT, padx=(10, 0))
        self.progress = ttk.Progressbar(counter_frame, mode='determinate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 10), fill=tk.X, expand=True)
        self.terminal = scrolledtext.ScrolledText(log_frame, height=4, state=tk.DISABLED)
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.terminal.configure(bg='#3e3e3e', fg='#ffffff', insertbackground='white')

        # --- Xray Status Frame (inside bottom container) ---
        xray_frame = ttk.LabelFrame(bottom_frame_container, text="Xray Status")
        xray_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.xray_terminal = scrolledtext.ScrolledText(xray_frame, height=4, state=tk.DISABLED)
        self.xray_terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.xray_terminal.configure(bg='#1e1e1e', fg='#cccccc', insertbackground='white')
        
        main_pane.paneconfigure(self.middle_frame, minsize=200)
        main_pane.paneconfigure(bottom_frame_container, minsize=150)
        
    def setup_logging(self):
        self.log_thread = threading.Thread(target=self.process_logs, daemon=True)
        self.log_thread.start()
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")
        
    def process_logs(self):
        while True:
            try:
                message = self.log_queue.get(timeout=0.1)
                self.root.after(0, self.update_terminal, message)
            except queue.Empty:
                continue
                
    def update_terminal(self, message):
        self.terminal.config(state=tk.NORMAL)
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)

    def setup_xray_logging(self):
        """Initializes the logging system for Xray-specific output."""
        self.xray_log_thread = threading.Thread(target=self.process_xray_logs, daemon=True)
        self.xray_log_thread.start()

    def log_xray(self, message):
        """Adds an Xray-specific log message to its queue."""
        self.xray_log_queue.put(message)

    def process_xray_logs(self):
        """Processes Xray log messages from the queue and updates the UI."""
        while True:
            try:
                message = self.xray_log_queue.get(timeout=0.1)
                self.root.after(0, self.update_xray_terminal, message)
            except queue.Empty:
                continue

    def update_xray_terminal(self, message):
        """Updates the Xray status terminal with a new message."""
        self.xray_terminal.config(state=tk.NORMAL)
        self.xray_terminal.insert(tk.END, message + "\n")
        self.xray_terminal.see(tk.END)
        self.xray_terminal.config(state=tk.DISABLED)

    def _stream_process_output(self, process, logger_func):
        """
        Reads stdout of a given process line-by-line in a separate thread
        and logs it using the provided logging function.
        """
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    logger_func(line.strip())
            process.stdout.close()
        except Exception as e:
            logger_func(f"Error reading process stream: {e}")
    
    def parse_config_info(self, config_uri):
        """Extract basic info from config URI"""
        try:
            if config_uri.startswith("vmess://"):
                base64_str = config_uri[8:]
                padded = base64_str + '=' * (4 - len(base64_str) % 4)
                decoded = base64.urlsafe_b64decode(padded).decode('utf-8')
                vmess_config = json.loads(decoded)
                return "vmess", vmess_config.get("add", "unknown"), vmess_config.get("port", "unknown")
            elif config_uri.startswith("vless://"):
                parsed = urllib.parse.urlparse(config_uri)
                return "vless", parsed.hostname or "unknown", parsed.port or "unknown"
            elif config_uri.startswith("ss://"):
                return "shadowsocks", "unknown", "unknown"
            elif config_uri.startswith("trojan://"):
                parsed = urllib.parse.urlparse(config_uri)
                return "trojan", parsed.hostname or "unknown", parsed.port or "unknown"
        except:
            pass
        return "unknown", "unknown", "unknown"
    
    def clear_temp_folder(self):
        """Clear all files in the temp folder"""
        try:
            for filename in os.listdir(self.TEMP_FOLDER):
                file_path = os.path.join(self.TEMP_FOLDER, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    self.log(f"Failed to delete {file_path}: {e}")
        except Exception as e:
            self.log(f"Error clearing temp folder: {e}")
            
    def stop_fetching(self):
        """Stop all fetching and testing operations"""
        self.is_fetching = False
        self.fetch_btn.config(text="Fetch & Test New Configs", style='TButton')
        self.log("Stopping all operations...")
        
        self.stop_event.set()
        
        self.kill_existing_xray_processes()
        self.clear_temp_folder()
        
        with self.thread_lock:
            for thread in self.active_threads[:]:
                if thread.is_alive():
                    thread.join(timeout=0.5)
                    if thread.is_alive():
                        self.log(f"Thread {thread.name} didn't stop gracefully")
        
        with self.thread_lock:
            self.active_threads.clear()
        
        self.stop_event.clear()
        self.log("All operations stopped")
        self.fetch_btn.config(state=tk.NORMAL)
        self.reload_btn.config(state=tk.NORMAL)
        self.progress.config(value=0)
    
    def fetch_and_test_configs(self):
        kill_xray_processes()
        if not self.is_fetching:
            self.stop_event.clear()
            self.show_mirror_selection()
        else:
            self.stop_fetching()
        
    def _fetch_and_test_worker(self):
        """Worker thread for fetching and testing configs"""
        try:
            with self.thread_lock:
                self.active_threads.append(threading.current_thread())
            
            self.log("Fetching configs from GitHub...")
            configs = self.fetch_configs()
            if not configs or self.stop_event.is_set():
                self.log("Operation stopped or no configs found")
                return
                
            self.total_configs = len(configs)
            self.tested_configs = 0
            self.working_configs = 0
            self.root.after(0, self.update_counters)
            
            self.log(f"Found {len(configs)} configs to test")
            self.root.after(0, lambda: self.progress.config(maximum=len(configs), value=0))
            
            existing_configs = set()
            if os.path.exists(self.BEST_CONFIGS_FILE):
                with open(self.BEST_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                    existing_configs = {line.strip() for line in f if line.strip()}
            
            self.log("Testing configs for latency...")
            best_configs = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.LATENCY_WORKERS) as executor:
                futures = {executor.submit(self.measure_latency, config): config for config in configs}
                for future in concurrent.futures.as_completed(futures):
                    if self.stop_event.is_set():
                        for f in futures:
                            f.cancel()
                        break
                        
                    result = future.result()
                    self.tested_configs += 1
                    
                    if result[1] != float('inf'):
                        config_uri = result[0]
                        if (not any(x[0] == config_uri for x in best_configs) and 
                            config_uri not in existing_configs):
                            
                            best_configs.append(result)
                            self.working_configs += 1
                            existing_configs.add(config_uri)
                            
                            with open(self.BEST_CONFIGS_FILE, 'a', encoding='utf-8') as f:
                                f.write(f"{config_uri}\n")
                                
                            self.log(f"Working config found: {result[1]:.2f}ms - added to best configs")
                            self.best_configs = sorted(best_configs, key=lambda x: x[1])
                            self.root.after(0, self.update_treeview)
                        
                    self.root.after(0, lambda: self.progress.config(value=self.tested_configs))
                    self.root.after(0, self.update_counters)
            
            self.best_configs = sorted(best_configs, key=lambda x: x[1])
            with open(self.WORKING_CONFIGS_FILE, "w", encoding='utf-8') as f:
                f.write("\n".join([uri for uri, _ in self.best_configs]))
                
            self.root.after(0, self.update_treeview)
            self.log(f"Testing complete! Found {len(self.best_configs)} working configs")
            
        except Exception as e:
            if not self.stop_event.is_set():
                self.log(f"Error in fetch and test: {str(e)}")
        finally:
            with self.thread_lock:
                if threading.current_thread() in self.active_threads:
                    self.active_threads.remove(threading.current_thread())
                    
            if not self.stop_event.is_set():
                self.root.after(0, lambda: self.fetch_btn.config(
                    text="Fetch & Test New Configs", state=tk.NORMAL, style='TButton'
                ))
                self.root.after(0, lambda: self.reload_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.progress.config(value=0))
                self.is_fetching = False
            
    def update_treeview(self):
        """Update the treeview with best configs"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        max_configs = min(100, len(self.best_configs))
        for i, (config_uri, latency) in enumerate(self.best_configs[:max_configs]):
            protocol, server, port = self.parse_config_info(config_uri)
            tags = ('connected',) if self.connected_config and config_uri == self.connected_config else ()
            self.tree.insert('', 'end', values=(
                i + 1, f"{latency:.2f}", protocol, server, port, config_uri
            ), tags=tags)
            
        self.log(f"Updated treeview with {max_configs} best configs")
        
    def on_tree_click(self, event):
        self.tree.after_idle(lambda: self.on_config_highlight(event))
    
    def on_config_highlight(self, event):
        """Handle single-click on treeview item"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            index = int(item['values'][0]) - 1
            if 0 <= index < len(self.best_configs):
                self.selected_config = self.best_configs[index][0]
                self.log(f"Selected config: {self.selected_config[:60]}...")
                self.connect_btn.config(state=tk.NORMAL)
                self.update_connection_status(self.is_connected)
                
    def on_config_select(self, event):
        """Handle double-click on treeview item"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            index = int(item['values'][0]) - 1
            if 0 <= index < len(self.best_configs):
                self.selected_config = self.best_configs[index][0]
                self.log(f"Selected config: {self.selected_config[:60]}...")
                self.connect_config()
                
    def connect_config(self):
        kill_xray_processes()
        self.update_connection_status(True)
        self.status_label.config(text="Connecting....", foreground="white")
        
        if not self.selected_config:
            messagebox.showwarning("Warning", "Please select a config first")
            return
            
        if self.is_connected:
            self.log("Already connected. Disconnecting first...")
            self.disconnect_config()
        
        self.set_proxy("127.0.0.1","1080")
        self.log("Attempting to connect...")
        
        self.connected_config = self.selected_config
        self.update_treeview()
    
        thread = threading.Thread(target=self._connect_worker, daemon=True)
        thread.start()
        
    def _connect_worker(self):
        """Worker thread for connecting"""
        try:
            config = self.parse_protocol(self.selected_config)
            with open(self.TEMP_CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(config, f)
                
            self.log("Starting Xray process...")
            
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.xray_process = subprocess.Popen(
                [self.XRAY_PATH, "run", "-config", self.TEMP_CONFIG_FILE],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Redirect stderr to stdout
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                startupinfo=startupinfo
            )
            
            time.sleep(2)
            
            if self.xray_process.poll() is None:
                self.is_connected = True
                self.root.after(0, self.update_connection_status, True)
                self.log("Connected successfully!")
                monitor_thread = threading.Thread(target=self._monitor_xray, daemon=True)
                monitor_thread.start()
            else:
                self.log("Failed to start Xray. Check Xray Status panel for details.")
                self.xray_process = None
                
        except Exception as e:
            self.log(f"Connection error: {str(e)}")
            
    def _monitor_xray(self):
        """Monitor Xray process output and log to the Xray terminal."""
        if self.xray_process:
            self._stream_process_output(self.xray_process, self.log_xray)
                    
    def update_connection_status(self, connected):
        """Update connection status in GUI"""
        if connected:
            self.status_label.config(text="Connected", foreground="SpringGreen")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Disconnected", foreground="Tomato")
            self.connect_btn.config(state=tk.NORMAL if self.selected_config else tk.DISABLED)
            self.disconnect_btn.config(state=tk.DISABLED)
    
    def disconnect_config(self, click_button=False):
        """Disconnect from current config"""
        if not self.is_connected:
            messagebox.showinfo("Info", "Not connected")
            return
        
        self.unset_proxy()
        self.log("Disconnecting...")
        
        if self.xray_process:
            try:
                self.xray_process.terminate()
                self.xray_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.xray_process.kill()
            except Exception as e:
                self.log(f"Error terminating process: {str(e)}")
            finally:
                self.xray_process = None
                
        self.is_connected = False
        self.connected_config = None
        if click_button :
            self.update_connection_status(False)
        else :
            self.status_label.config(text="Connecting....", foreground="white")
        
        try:
            if os.path.exists(self.TEMP_CONFIG_FILE):
                os.remove(self.TEMP_CONFIG_FILE)
        except:
            pass
            
        self.update_treeview()
        self.log("Disconnected")
        
    def click_disconnect_config_button(self) :
        self.update_connection_status(False)
        self.disconnect_config(True)
    
    def set_proxy(self, proxy_server, port):
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            access = winreg.KEY_WRITE
            with winreg.OpenKey(key, subkey, 0, access) as internet_settings_key:
                winreg.SetValueEx(internet_settings_key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(internet_settings_key, "ProxyServer", 0, winreg.REG_SZ, f"{proxy_server}:{port}")
        except Exception as e:
            pass

    def unset_proxy(self):
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            access = winreg.KEY_WRITE
            with winreg.OpenKey(key, subkey, 0, access) as internet_settings_key:
                winreg.SetValueEx(internet_settings_key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.DeleteValue(internet_settings_key, "ProxyServer")
        except Exception as e:
            pass
    
    # Method restored here
    def kill_existing_xray_processes(self):
        """Kill any existing Xray processes"""
        try:
            if sys.platform == 'win32':
                # Windows implementation
                import psutil
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'] == 'xray.exe':
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                # Linux/macOS implementation
                import signal
                import subprocess
                subprocess.run(['pkill', '-f', 'xray'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            # Cannot log here as logging might not be set up yet
            print(f"Error killing existing Xray processes: {str(e)}")

    def vmess_to_json(self, vmess_url):
        if not vmess_url.startswith("vmess://"):
            raise ValueError("Invalid VMess URL format")
        
        base64_str = vmess_url[8:]
        padded = base64_str + '=' * (4 - len(base64_str) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        decoded_str = decoded_bytes.decode('utf-8')
        vmess_config = json.loads(decoded_str)
        
        xray_config = {
            "inbounds": [{"port": self.SOCKS_PORT, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}],
            "outbounds": [{"protocol": "vmess", "settings": {"vnext": [{"address": vmess_config["add"], "port": int(vmess_config["port"]), "users": [{"id": vmess_config["id"], "alterId": int(vmess_config.get("aid", 0)), "security": vmess_config.get("scy", "auto")}]}]}, "streamSettings": {"network": vmess_config.get("net", "tcp"), "security": vmess_config.get("tls", ""), "tcpSettings": {"header": {"type": vmess_config.get("type", "none"), "request": {"path": [vmess_config.get("path", "/")], "headers": {"Host": [vmess_config.get("host", "")]}}}} if vmess_config.get("net") == "tcp" and vmess_config.get("type") == "http" else None}}]
        }
        
        if not xray_config["outbounds"][0]["streamSettings"]["security"]:
            del xray_config["outbounds"][0]["streamSettings"]["security"]
        if not xray_config["outbounds"][0]["streamSettings"].get("tcpSettings"):
            xray_config["outbounds"][0]["streamSettings"].pop("tcpSettings", None)
        
        return xray_config

    def parse_vless(self, uri):
        parsed = urllib.parse.urlparse(uri)
        config = {
            "inbounds": [{"port": self.SOCKS_PORT, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}],
            "outbounds": [{"protocol": "vless", "settings": {"vnext": [{"address": parsed.hostname, "port": parsed.port, "users": [{"id": parsed.username, "encryption": parse_qs(parsed.query).get("encryption", ["none"])[0]}]}]}, "streamSettings": {"network": parse_qs(parsed.query).get("type", ["tcp"])[0], "security": parse_qs(parsed.query).get("security", ["none"])[0]}}]
        }
        return config

    def parse_shadowsocks(self, uri):
        if not uri.startswith("ss://"):
            raise ValueError("Invalid Shadowsocks URI")
        
        parts = uri[5:].split("#", 1)
        encoded_part = parts[0]
        
        if "@" in encoded_part:
            userinfo, server_part = encoded_part.split("@", 1)
        else:
            decoded = base64.b64decode(encoded_part + '=' * (-len(encoded_part) % 4)).decode('utf-8')
            if "@" in decoded:
                userinfo, server_part = decoded.split("@", 1)
            else:
                userinfo = decoded; server_part = ""

        if ":" in server_part:
            server, port = server_part.rsplit(":", 1); port = int(port)
        else:
            server = server_part; port = 443

        try:
            decoded_userinfo = base64.b64decode(userinfo + '=' * (-len(userinfo) % 4)).decode('utf-8')
        except:
            decoded_userinfo = base64.b64decode(encoded_part + '=' * (-len(encoded_part) % 4)).decode('utf-8')
            if "@" in decoded_userinfo:
                userinfo_part, server_part = decoded_userinfo.split("@", 1)
                if ":" in server_part:
                    server, port = server_part.rsplit(":", 1); port = int(port)
                decoded_userinfo = userinfo_part

        if ":" not in decoded_userinfo: raise ValueError("Invalid Shadowsocks URI")
        method, password = decoded_userinfo.split(":", 1)

        return {"inbounds": [{"port": self.SOCKS_PORT, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}], "outbounds": [{"protocol": "shadowsocks", "settings": {"servers": [{"address": server, "port": port, "method": method, "password": password}]}, "tag": "proxy"}, {"protocol": "freedom", "tag": "direct"}], "routing": {"domainStrategy": "IPOnDemand", "rules": [{"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"}]}}

    def parse_trojan(self, uri):
        if not uri.startswith("trojan://"): raise ValueError("Invalid Trojan URI")
        parsed = urllib.parse.urlparse(uri)
        password = parsed.username; server = parsed.hostname; port = parsed.port
        query = parse_qs(parsed.query)
        return {"inbounds": [{"port": self.SOCKS_PORT, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}], "outbounds": [{"protocol": "trojan", "settings": {"servers": [{"address": server, "port": port, "password": password}]}, "streamSettings": {"network": query.get("type", ["tcp"])[0], "security": "tls", "tcpSettings": {"header": {"type": query.get("headerType", ["none"])[0], "request": {"headers": {"Host": [query.get("host", [""])[0]]}}}}}, "tag": "proxy"}, {"protocol": "freedom", "tag": "direct"}], "routing": {"domainStrategy": "IPOnDemand", "rules": [{"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"}]}}

    def parse_protocol(self, uri):
        if uri.startswith("vmess://"): return self.vmess_to_json(uri)
        elif uri.startswith("vless://"): return self.parse_vless(uri)
        elif uri.startswith("ss://"): return self.parse_shadowsocks(uri)
        elif uri.startswith("trojan://"): return self.parse_trojan(uri)
        raise ValueError("Unsupported protocol")

    def is_port_available(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try: s.bind(('127.0.0.1', port)); return True
            except: return False

    def get_available_port(self):
        for _ in range(10):
            port = random.randint(49152, 65535)
            if self.is_port_available(port): return port
        return 1080

    def measure_latency(self, config_uri):
        if self.stop_event.is_set():
            return (config_uri, float('inf'))
            
        try:
            socks_port = self.get_available_port()
            if socks_port is None: socks_port = 1080 + random.randint(1, 100)
            
            config = self.parse_protocol(config_uri)
            config['inbounds'][0]['port'] = socks_port
            
            rand_suffix = random.randint(100000, 999999)
            temp_config_file = os.path.join(self.TEMP_FOLDER, f"temp_config_{rand_suffix}.json")
            
            with open(temp_config_file, "w", encoding='utf-8') as f: json.dump(config, f)
                
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            xray_process = subprocess.Popen(
                [self.XRAY_PATH, "run", "-config", temp_config_file],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                startupinfo=startupinfo
            )
            
            output_monitor = threading.Thread(target=self._stream_process_output, args=(xray_process, self.log_xray), daemon=True)
            output_monitor.start()

            if self.stop_event.is_set():
                xray_process.terminate()
                try: os.remove(temp_config_file)
                except: pass
                return (config_uri, float('inf'))
                
            time.sleep(0.1)
            
            proxies = {'http': f'socks5://127.0.0.1:{socks_port}', 'https': f'socks5://127.0.0.1:{socks_port}'}
            latency = float('inf')
            try:
                start_time = time.perf_counter()
                response = requests.get(self.PING_TEST_URL, proxies=proxies, timeout=4, headers={'Cache-Control': 'no-cache', 'Connection': 'close'})
                if response.status_code == 200:
                    latency = (time.perf_counter() - start_time) * 1000
            except requests.RequestException: pass
            finally:
                xray_process.terminate()
                try: xray_process.wait(timeout=2)
                except subprocess.TimeoutExpired: xray_process.kill()
                try: os.remove(temp_config_file)
                except: pass
                time.sleep(0.1)
            
            return (config_uri, latency)
        
        except Exception as e:
            return (config_uri, float('inf'))

    def fetch_configs(self):
        try:
            response = requests.get(self.CONFIGS_URL)
            response.raise_for_status()
            response.encoding = 'utf-8'
            configs = [line.strip() for line in response.text.splitlines() if line.strip()]
            return configs[::-1]
        except Exception as e:
            return []

def main():
    kill_xray_processes()
    root = tk.Tk()
    app = VPNConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
