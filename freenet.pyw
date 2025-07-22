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
import threading
import queue
import sys
from datetime import datetime
import platform
if platform.system() == "Windows":
    import winreg
import qrcode
import zipfile
import shutil
from PIL import ImageTk, Image
if sys.platform == 'win32':
    from subprocess import CREATE_NO_WINDOW



def kill_xray_processes():
        """Kill any existing Xray processes"""
        try:
            if sys.platform == 'win32':
                import psutil
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'].lower() == 'xray.exe':
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                import subprocess
                subprocess.run(['pkill', '-f', 'xray'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


class VPNConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN Config Manager")
<<<<<<< HEAD
        self.root.geometry("600x600+620+20")
=======
        self.root.geometry("600x600+620+20") # بازگشت به اندازه استاندارد
>>>>>>> 882839400a3e2228cb7652fe05173040517d44b9
        
        self.setup_dark_theme()
        
        self.log_queue = queue.Queue()
        
        self.kill_existing_xray_processes()

        self.stop_event = threading.Event()
        self.thread_lock = threading.Lock()
        self.active_threads = []
        self.is_fetching = False
        
<<<<<<< HEAD
        self.XRAY_CORE_URL = self._get_xray_core_url()
        self.XRAY_PATH = os.path.join(os.getcwd(), "xray.exe" if sys.platform == 'win32' else "xray")
        
=======
>>>>>>> 882839400a3e2228cb7652fe05173040517d44b9
        self.setup_ui()
        self.setup_logging()

        self.XRAY_LOG_FILE = "xraylog.txt"
        self.load_mirrors()
        
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
        self.TEST_TIMEOUT = 10
        self.SOCKS_PORT = 1080
        self.PING_TEST_URL = "https://facebook.com"
        self.LATENCY_WORKERS = 100
        
        if not os.path.exists(self.TEMP_FOLDER):
            os.makedirs(self.TEMP_FOLDER)
        
        self.best_configs = []
        self.selected_config = None
        self.connected_config = None
        self.xray_process = None
        self.is_connected = False
        self.is_connecting = False
        self.total_configs = 0
        self.tested_configs = 0
        self.working_configs = 0
        
        if os.path.exists(self.BEST_CONFIGS_FILE):
            self.load_best_configs()

    def _get_xray_core_url(self):
        system = platform.system().lower()
        machine = platform.machine().lower()
        base_url = "https://github.com/XTLS/Xray-core/releases/latest/download/"
        
        filename = ""
        if system == "windows":
            if machine in ["amd64", "x86_64"]: filename = "Xray-windows-64.zip"
            elif machine in ["i386", "i686", "x86"]: filename = "Xray-windows-32.zip"
            elif machine in ["arm64", "aarch64"]: filename = "Xray-windows-arm64-v8a.zip"
        elif system == "linux":
            if machine in ["amd64", "x86_64"]: filename = "Xray-linux-64.zip"
            elif machine in ["arm64", "aarch64"]: filename = "Xray-linux-arm64-v8a.zip"
        elif system == "darwin": # macOS
            if machine in ["arm64", "aarch64"]: filename = "Xray-macos-arm64-v8a.zip"
            elif machine in ["amd64", "x86_64"]: filename = "Xray-macos-64.zip"

        if not filename:
            self.log(f"Unsupported OS/Arch: {system}/{machine}. Please install Xray manually.")
            return ""
            
        return base_url + filename
            
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
            lines = []
            with open(subs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    cleaned_line = line.strip()
                    if cleaned_line and not cleaned_line.startswith('#'):
                        if cleaned_line.endswith(','):
                            cleaned_line = cleaned_line[:-1]
                        lines.append(cleaned_line)
            
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
        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        options_menu = tk.Menu(menubar, tearoff=0)
        options_menu.add_command(label="Update Xray Core", command=self.update_xray_core)
        options_menu.add_command(label="Update GeoFiles", command=self.update_geofiles)
        menubar.add_cascade(label="Options", menu=options_menu)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Clear Terminal", command=self.clear_terminal)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        self.root.config(menu=menubar)

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

        # --- Bottom Logs Frame (Bottom Pane) ---
        log_frame = ttk.LabelFrame(main_pane, text="Logs")
        main_pane.add(log_frame)

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
        self.terminal = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.terminal.configure(bg='#3e3e3e', fg='#ffffff', insertbackground='white')
        
        main_pane.paneconfigure(self.middle_frame, minsize=200)
        main_pane.paneconfigure(log_frame, minsize=150)
        
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

    def log_xray(self, message):
        """Adds an Xray-specific log message directly to its file."""
        try:
            with open(self.XRAY_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            # Cannot use self.log here as it might be called from a thread
            # and could cause race conditions with the UI.
            print(f"Error writing to xray log file: {e}")

    def _clear_xray_log_file(self):
        """Clears the xray log file and writes a header."""
        try:
            with open(self.XRAY_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write(f"--- Xray Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        except Exception as e:
            self.log(f"Could not clear xray log file: {e}")

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
            self._clear_xray_log_file()
            self.stop_event.clear()
            self.show_mirror_selection()
        else:
            self.stop_fetching()

    def show_mirror_selection(self):
        """Show a popup window to select mirror and thread count"""
        self.mirror_window = tk.Toplevel(self.root)
        self.mirror_window.title("Select Mirror & Threads")
        self.mirror_window.geometry("300x200")
        self.mirror_window.resizable(False, False)
        
        window_width, window_height = 300, 200
        screen_width, screen_height = self.mirror_window.winfo_screenwidth(), self.mirror_window.winfo_screenheight()
        x, y = int((screen_width/2) - (window_width/2)), int((screen_height/2) - (window_height/2))
        self.mirror_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.mirror_window.tk_setPalette(background='#2d2d2d', foreground='#ffffff', activeBackground='#3e3e3e', activeForeground='#ffffff')
        
        ttk.Label(self.mirror_window, text="Select a mirror:").pack(pady=(10, 0))
        self.mirror_combo = ttk.Combobox(self.mirror_window, values=list(self.MIRRORS.keys()), state="readonly", style='TCombobox')
        self.mirror_combo.current(0)
        self.mirror_combo.pack(pady=5, padx=20, fill=tk.X)
        
        ttk.Label(self.mirror_window, text="Maximum cpu usage:").pack(pady=(10, 0))
        self.thread_combo = ttk.Combobox(self.mirror_window, values=["10", "20", "50", "100"], state="readonly", style='TCombobox')
        self.thread_combo.set("100")
        self.thread_combo.pack(pady=5, padx=20, fill=tk.X)
        
        self.mirror_window.option_add('*TCombobox*Listbox.background', '#3e3e3e')
        self.mirror_window.option_add('*TCombobox*Listbox.foreground', '#ffffff')
        self.mirror_window.option_add('*TCombobox*Listbox.selectBackground', '#4a6984')
        self.mirror_window.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
        
        button_frame = ttk.Frame(self.mirror_window)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=self.on_mirror_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_mirror_selection).pack(side=tk.LEFT, padx=5)
        
        self.mirror_window.protocol("WM_DELETE_WINDOW", self.cancel_mirror_selection)
        self.mirror_window.grab_set()
        self.mirror_window.transient(self.root)
        self.mirror_window.wait_window(self.mirror_window)

    def cancel_mirror_selection(self):
        if hasattr(self, 'mirror_window') and self.mirror_window:
            self.mirror_window.destroy()
        self.fetch_btn.config(text="Fetch & Test New Configs", style='TButton', state=tk.NORMAL)
        self.is_fetching = False

    def on_mirror_selected(self):
        selected_mirror = self.mirror_combo.get()
        selected_threads = self.thread_combo.get()
        if selected_mirror in self.MIRRORS:
            self.CONFIGS_URL = self.MIRRORS[selected_mirror]
            try:
                self.LATENCY_WORKERS = int(selected_threads)
            except ValueError:
                self.LATENCY_WORKERS = 100
            self.log(f"Selected mirror: {selected_mirror}, Threads: {self.LATENCY_WORKERS}")
            self.mirror_window.destroy()
            self._start_fetch_and_test()
        else:
            self.cancel_mirror_selection()

    def _start_fetch_and_test(self):
        self.is_fetching = True
        self.fetch_btn.config(text="Stop Fetching Configs", style='Stop.TButton')
        self.log("Starting config fetch and test...")
        self.stop_event.clear()
        thread = threading.Thread(target=self._fetch_and_test_worker, daemon=True)
        thread.start()

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.on_config_highlight(event)
            try:
                self.generate_qrcode()
            except:
                pass

    def load_best_configs(self):
        try:
            if os.path.exists(self.BEST_CONFIGS_FILE):
                with open(self.BEST_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                    seen, config_uris = [], []
                    for line in f:
                        line = line.strip()
                        if line and line not in seen:
                            seen.append(line)
                            config_uris.append(line)
                    if config_uris:
                        self.best_configs = [(uri, float('inf')) for uri in config_uris]
                        self.total_configs = len(config_uris)
                        self.tested_configs = 0
                        self.working_configs = 0
                        self.update_counters()
                        self.root.after(0, lambda: self.progress.config(maximum=len(config_uris), value=0))
                        self.log(f"Loaded {len(config_uris)} configs from {self.BEST_CONFIGS_FILE}")
                        thread = threading.Thread(target=self._test_pasted_configs_worker, args=(config_uris,), daemon=True)
                        thread.start()
        except Exception as e:
            self.log(f"Error loading best configs: {str(e)}")

    def reload_and_test_configs(self):
        self.reload_btn.config(state=tk.DISABLED)
        self.log("Reloading and testing configs from best_configs.txt...")
        self.best_configs = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._clear_xray_log_file()
        self.load_best_configs()

    def delete_selected_configs(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items: return
        selected_uris = [self.tree.item(item)['values'][5] for item in selected_items]
        try:
            with open(self.BEST_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                all_configs = [line.strip() for line in f if line.strip()]
            remaining_configs, deleted_count = [], 0
            for config in all_configs:
                if config not in selected_uris:
                    remaining_configs.append(config)
                else:
                    deleted_count += 1
            with open(self.BEST_CONFIGS_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(remaining_configs))
            self.best_configs = []
            self.load_best_configs()
            self.log(f"Deleted {deleted_count} config(s)")
        except Exception as e:
            self.log(f"Error deleting configs: {str(e)}")

    def save_best_configs(self):
        try:
            with open(self.BEST_CONFIGS_FILE, 'w', encoding='utf-8') as f:
                for config_uri, _ in self.best_configs:
                    f.write(f"{config_uri}\n")
        except Exception as e:
            self.log(f"Error saving best configs: {str(e)}")

    def generate_qrcode(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items: return
        item = selected_items[0]
        index = int(self.tree.item(item)['values'][0]) - 1
        if 0 <= index < len(self.best_configs):
            config_uri = self.best_configs[index][0]
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(config_uri)
            qr.make(fit=True)
            self.original_img = qr.make_image(fill_color="black", back_color="white")
            qr_window = tk.Toplevel(self.root)
            qr_window.title("Config QR Code")
            qr_window.geometry("600x620+20+20")
            self.tk_image = ImageTk.PhotoImage(self.original_img)
            self.label = ttk.Label(qr_window, image=self.tk_image)
            self.label.image = self.tk_image
            self.label.pack(pady=10)
            if config_uri.startswith("vmess://"):
                self.zoom_level = 0.7
                width, height = self.original_img.size
                new_size = (int(width * self.zoom_level), int(height * self.zoom_level))
                resized_img = self.original_img.resize(new_size, Image.Resampling.LANCZOS)
                self.tk_image = ImageTk.PhotoImage(resized_img)
                self.label.configure(image=self.tk_image)
                self.label.image = self.tk_image
            else:
                self.zoom_level = 1.0
            qr_window.bind("<Control-MouseWheel>", self.zoom_qrcode)
            self.label.bind("<Control-MouseWheel>", self.zoom_qrcode)
            config_preview = ttk.Label(qr_window, text=config_uri[:40] + "..." if len(config_uri) > 40 else config_uri, wraplength=280)
            config_preview.pack(pady=5, padx=10)
            close_btn = ttk.Button(qr_window, text="Close", command=qr_window.destroy)
            close_btn.pack(pady=5)

    def zoom_qrcode(self, event):
        self.zoom_level *= 1.1 if event.delta > 0 else 0.9
        self.zoom_level = max(0.1, min(self.zoom_level, 5.0))
        width, height = self.original_img.size
        new_size = (int(width * self.zoom_level), int(height * self.zoom_level))
        resized_img = self.original_img.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_img)
        self.label.configure(image=self.tk_image)
        self.label.image = self.tk_image

    def paste_configs(self, event=None):
        try:
            clipboard = self.root.clipboard_get()
            if clipboard.strip():
                configs = [line.strip() for line in clipboard.splitlines() if line.strip()]
                if configs:
                    self.log(f"Pasted {len(configs)} config(s) from clipboard")
                    self._test_pasted_configs(configs)
        except tk.TclError:
            pass

    def _test_pasted_configs(self, configs):
        self.fetch_btn.config(state=tk.DISABLED)
        self.log("Testing pasted configs...")
        self._clear_xray_log_file()
        thread = threading.Thread(target=self._test_pasted_configs_worker, args=(configs,), daemon=True)
        thread.start()

    def _test_pasted_configs_worker(self, configs):
        try:
            self.total_configs = len(configs)
            self.tested_configs, self.working_configs = 0, 0
            self.root.after(0, self.update_counters)
            self.root.after(0, lambda: self.progress.config(maximum=len(configs), value=0))
            best_configs, all_tested_configs = [], []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.LATENCY_WORKERS) as executor:
                futures = {executor.submit(self.measure_latency, config): config for config in configs}
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    self.tested_configs += 1
                    all_tested_configs.append(result)
                    if result[1] != float('inf'):
                        existing_index = next((i for i, (uri, _) in enumerate(best_configs) if uri == result[0]), None)
                        if existing_index is not None:
                            if result[1] < best_configs[existing_index][1]:
                                best_configs[existing_index] = result
                                self.log(f"Updated config latency: {result[1]:.2f}ms")
                        else:
                            best_configs.append(result)
                            self.working_configs += 1
                            self.log(f"Working config found: {result[1]:.2f}ms")
                    self.root.after(0, lambda: self.progress.config(value=self.tested_configs))
                    self.root.after(0, self.update_counters)
            self.best_configs = [config for config in best_configs if config[1] != float('inf')]
            self.best_configs.sort(key=lambda x: x[1])
            with open(self.BEST_CONFIGS_FILE, 'w', encoding='utf-8') as f:
                for config_uri, _ in all_tested_configs:
                    f.write(f"{config_uri}\n")
            self.root.after(0, self.update_treeview)
            self.log(f"Testing complete! Found {len(self.best_configs)} working configs")
        except Exception as e:
            self.log(f"Error in testing pasted configs: {str(e)}")
        finally:
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.reload_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.progress.config(value=0))

    def copy_selected_configs(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items: return
        configs = []
        for item in selected_items:
            index = int(self.tree.item(item)['values'][0]) - 1
            if 0 <= index < len(self.best_configs):
                configs.append(self.best_configs[index][0])
        if configs:
            self.root.clipboard_clear()
            self.root.clipboard_append('\n'.join(configs))
            self.log(f"Copied {len(configs)} config(s) to clipboard")

    def update_counters(self):
        self.tested_label.config(text=f"Tested: {self.tested_configs}")
        self.total_label.config(text=f"Total: {self.total_configs}")
        self.working_label.config(text=f"Working: {self.working_configs}")
        
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
                self.update_connection_status()
                
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
        if self.is_connecting or self.is_fetching: return

        kill_xray_processes()
        self._clear_xray_log_file()
        
        if not self.selected_config:
            messagebox.showwarning("Warning", "Please select a config first")
            return
            
        if self.is_connected:
            self.log("Already connected. Disconnecting first...")
            self.disconnect_config()
        
        self.is_connecting = True
        self.update_connection_status()
        
        self.connected_config = self.selected_config
        self.update_treeview()
    
        thread = threading.Thread(target=self._connect_worker, daemon=True)
        thread.start()
        
    def _connect_worker(self):
        """Worker thread for connecting"""
        try:
            self.set_proxy("127.0.0.1", "1080")
            self.log("Attempting to connect...")

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
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                startupinfo=startupinfo
            )
            
            time.sleep(2)
            
            if self.xray_process.poll() is None:
                self.is_connected = True
                self.log("Connected successfully!")
                monitor_thread = threading.Thread(target=self._monitor_xray, daemon=True)
                monitor_thread.start()
            else:
                self.is_connected = False
                self.log("Failed to start Xray. Check xraylog.txt for details.")
                self.xray_process = None
                self.unset_proxy()
                
        except Exception as e:
            self.is_connected = False
            self.log(f"Connection error: {str(e)}")
            self.unset_proxy()
        finally:
            self.is_connecting = False
            self.root.after(0, self.update_connection_status)

    def _monitor_xray(self):
        """Monitor Xray process output and log to the Xray terminal."""
        if self.xray_process:
            self._stream_process_output(self.xray_process, self.log_xray)
                    
    def update_connection_status(self):
        """Update connection status in GUI based on state variables."""
        if self.is_connecting:
            self.status_label.config(text="Connecting...", foreground="orange")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.fetch_btn.config(state=tk.DISABLED)
            self.reload_btn.config(state=tk.DISABLED)
        elif self.is_connected:
            self.status_label.config(text="Connected", foreground="SpringGreen")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.fetch_btn.config(state=tk.NORMAL)
            self.reload_btn.config(state=tk.NORMAL)
        else: # Disconnected
            self.status_label.config(text="Disconnected", foreground="Tomato")
            self.connect_btn.config(state=tk.NORMAL if self.selected_config else tk.DISABLED)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.fetch_btn.config(state=tk.NORMAL)
            self.reload_btn.config(state=tk.NORMAL)
    
    def disconnect_config(self, from_button=False):
        """Disconnect from current config"""
        if not self.is_connected:
            if from_button:
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
        
        try:
            if os.path.exists(self.TEMP_CONFIG_FILE):
                os.remove(self.TEMP_CONFIG_FILE)
        except:
            pass
            
        self.update_treeview()
        self.log("Disconnected")
        self.update_connection_status()
        
    def click_disconnect_config_button(self) :
        self.disconnect_config(from_button=True)
    
    def set_proxy(self, proxy_server, port):
        system = platform.system()
        try:
            if system == 'Windows':
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                access = winreg.KEY_WRITE
                with winreg.OpenKey(key, subkey, 0, access) as internet_settings_key:
                    winreg.SetValueEx(internet_settings_key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(internet_settings_key, "ProxyServer", 0, winreg.REG_SZ, f"{proxy_server}:{port}")
            elif system == 'Darwin': # macOS
                networks = subprocess.check_output(["networksetup", "-listallnetworkservices"]).decode('utf-8')
                for service in networks.split('\n')[1:]:
                    if service.strip():
                        subprocess.run(["networksetup", "-setsocksfirewallproxy", service.strip(), proxy_server, str(port)])
            elif system == 'Linux': # GNOME
                subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"])
                subprocess.run(["gsettings", "set", "org.gnome.system.proxy.socks", "host", proxy_server])
                subprocess.run(["gsettings", "set", "org.gnome.system.proxy.socks", "port", str(port)])
        except Exception as e:
            self.log(f"Failed to set system proxy: {e}")

    def unset_proxy(self):
        system = platform.system()
        try:
            if system == 'Windows':
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                access = winreg.KEY_WRITE
                with winreg.OpenKey(key, subkey, 0, access) as internet_settings_key:
                    winreg.SetValueEx(internet_settings_key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            elif system == 'Darwin': # macOS
                networks = subprocess.check_output(["networksetup", "-listallnetworkservices"]).decode('utf-8')
                for service in networks.split('\n')[1:]:
                    if service.strip():
                        subprocess.run(["networksetup", "-setsocksfirewallproxystate", service.strip(), "off"])
            elif system == 'Linux': # GNOME
                subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "none"])
        except Exception as e:
            self.log(f"Failed to unset system proxy: {e}")
    
    def kill_existing_xray_processes(self):
        """Kill any existing Xray processes"""
        try:
            if sys.platform == 'win32':
                import psutil
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'].lower() == 'xray.exe':
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                import subprocess
                subprocess.run(['pkill', '-f', 'xray'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
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
        query_params = parse_qs(parsed.query)
        uuid = urllib.parse.unquote(parsed.username)

        config = {
            "inbounds": [{"port": self.SOCKS_PORT, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}],
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": parsed.hostname,
                        "port": parsed.port,
                        "users": [{"id": uuid, "encryption": query_params.get("encryption", ["none"])[0]}]
                    }]
                },
                "streamSettings": {
                    "network": query_params.get("type", ["tcp"])[0],
                    "security": query_params.get("security", ["none"])[0]
                }
            }]
        }
        
        if config["outbounds"][0]["streamSettings"]["security"] == "reality":
            config["outbounds"][0]["streamSettings"]["realitySettings"] = {
                "serverName": query_params.get("sni", [""])[0],
                "publicKey": query_params.get("pbk", [""])[0],
                "shortId": query_params.get("sid", [""])[0]
            }
        return config

    def parse_shadowsocks(self, uri):
        if not uri.startswith("ss://"):
            raise ValueError("Invalid Shadowsocks URI")
        
        main_part = uri[5:].split("#", 1)[0]
        
        if "@" in main_part:
            user_info_part, server_part = main_part.split("@", 1)
        else:
            user_info_part = main_part
            server_part = ""

        try:
            decoded_userinfo = base64.urlsafe_b64decode(user_info_part + '=' * (-len(user_info_part) % 4)).decode('utf-8')
            method, password = decoded_userinfo.split(":", 1)
        except Exception:
             raise ValueError("Invalid user info in Shadowsocks URI")

        server_and_port = server_part.split("?", 1)[0]
        if ":" in server_and_port:
            server, port_str = server_and_port.rsplit(":", 1)
            port = int(port_str)
        else:
            raise ValueError("Invalid server/port in Shadowsocks URI")

        return {"inbounds": [{"port": self.SOCKS_PORT, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}], "outbounds": [{"protocol": "shadowsocks", "settings": {"servers": [{"address": server, "port": port, "method": method, "password": password}]}}]}

    def parse_trojan(self, uri):
        if not uri.startswith("trojan://"): raise ValueError("Invalid Trojan URI")
        parsed = urllib.parse.urlparse(uri)
        password = parsed.username; server = parsed.hostname; port = parsed.port
        query = parse_qs(parsed.query)
        return {"inbounds": [{"port": self.SOCKS_PORT, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}], "outbounds": [{"protocol": "trojan", "settings": {"servers": [{"address": server, "port": port, "password": password}]}, "streamSettings": {"network": query.get("type", ["tcp"])[0], "security": "tls", "tcpSettings": {"header": {"type": query.get("headerType", ["none"])[0], "request": {"headers": {"Host": [query.get("host", [""])[0]]}}}}}]}

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
            self.log_xray(f"--- Error parsing {config_uri[:30]}... ---\n{e}\n")
            return (config_uri, float('inf'))

    def fetch_configs(self):
        strategies = [
            ("System default", None),
            ("Google DNS", self._try_with_google_dns),
            ("Cloudflare DNS", self._try_with_cloudflare_dns),
            ("Direct IP", self._try_with_direct_ip),
        ]
        for strategy_name, strategy_func in strategies:
            self.log(f"Trying strategy: {strategy_name}")
            try:
                if strategy_func:
                    response = strategy_func()
                else:
                    response = requests.get(self.CONFIGS_URL, timeout=10)
                
                response.raise_for_status()
                response.encoding = 'utf-8'
                valid_prefixes = ("vmess://", "vless://", "ss://", "trojan://")
                configs = [line.strip() for line in response.text.splitlines() if line.strip().startswith(valid_prefixes)]
                self.log(f"Successfully fetched configs using: {strategy_name}")
                return configs[::-1]
            except Exception as e:
                self.log(f"Error with {strategy_name}: {str(e)}")
        
        self.log("All strategies failed")
        return []

    def _try_with_google_dns(self):
        return self._try_with_custom_dns(['8.8.8.8', '8.8.4.4'])

    def _try_with_cloudflare_dns(self):
        return self._try_with_custom_dns(['1.1.1.1', '1.0.0.1'])

    def _try_with_custom_dns(self, dns_servers):
        hostname = self.CONFIGS_URL.split('//')[1].split('/')[0]
        ip = self._resolve_hostname(hostname, dns_servers[0])
        url_with_ip = self.CONFIGS_URL.replace(hostname, ip)
        headers = {'Host': hostname}
        return requests.get(url_with_ip, headers=headers, timeout=10)

    def _resolve_hostname(self, hostname, dns_server):
        try: # dnspython
            import dns.resolver
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            result = resolver.resolve(hostname, 'A')
            return str(result[0])
        except: # system tools
            return self._resolve_with_system_tools(hostname, dns_server)

    def _resolve_with_system_tools(self, hostname, dns_server):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['nslookup', hostname, dns_server], capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if 'Address:' in line and dns_server not in line:
                        return line.split(':')[1].strip()
            else:
                result = subprocess.run(['dig', f'@{dns_server}', hostname, '+short'], capture_output=True, text=True, timeout=5)
                ip = result.stdout.strip().split('\n')[0]
                if ip and not ip.startswith(';'): return ip
        except: pass
        return socket.gethostbyname(hostname)

    def _try_with_direct_ip(self):
        github_ips = ['140.82.112.3', '140.82.114.3', '140.82.113.3', '140.82.121.4']
        hostname = self.CONFIGS_URL.split('//')[1].split('/')[0]
        for ip in github_ips:
            try:
                url_with_ip = self.CONFIGS_URL.replace(hostname, ip)
                headers = {'Host': hostname}
                return requests.get(url_with_ip, headers=headers, timeout=10)
            except: continue
        raise Exception("All direct IP attempts failed")

    def clear_terminal(self):
        self.terminal.config(state=tk.NORMAL)
        self.terminal.delete('1.0', tk.END)
        self.terminal.config(state=tk.DISABLED)

    def update_xray_core(self):
        self.log("Starting Xray core update...")
        thread = threading.Thread(target=self._update_xray_core_worker, daemon=True)
        thread.start()

    def _update_xray_core_worker(self):
        try:
            self.kill_existing_xray_processes()
            self.log("Downloading latest Xray core...")
            self.log(f"Using URL: {self.XRAY_CORE_URL}")
            
            response = requests.get(self.XRAY_CORE_URL, stream=True)
            response.raise_for_status()
            
            zip_path = os.path.join(self.TEMP_FOLDER, "xray_update.zip")
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            self.log("Extracting Xray core...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                executable_name = "xray.exe" if platform.system() == "Windows" else "xray"
                for file in zip_ref.namelist():
                    if file.lower().endswith(executable_name.lower()):
                        zip_ref.extract(file, self.TEMP_FOLDER)
                        extracted_path = os.path.join(self.TEMP_FOLDER, file)
                        shutil.move(extracted_path, self.XRAY_PATH)
                        if platform.system() != "Windows":
                            os.chmod(self.XRAY_PATH, 0o755)
                        break
            
            self.log("Xray core updated successfully!")
            messagebox.showinfo("Success", "Xray core updated successfully!")
        except Exception as e:
            self.log(f"Error updating Xray core: {str(e)}")
            messagebox.showerror("Error", f"Failed to update Xray core: {str(e)}")
        finally:
            if 'zip_path' in locals() and os.path.exists(zip_path):
                os.remove(zip_path)

    def update_geofiles(self):
        self.log("Starting GeoFiles update...")
        thread = threading.Thread(target=self._update_geofiles_worker, daemon=True)
        thread.start()

    def _update_geofiles_worker(self):
        files_to_download = {
            "geoip.dat": "https://github.com/v2fly/geoip/releases/latest/download/geoip.dat",
            "geosite.dat": "https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat"
        }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(self._download_file_segmented, url, filename, filename): filename for filename, url in files_to_download.items()}
            
            all_successful = True
            for future in concurrent.futures.as_completed(futures):
                filename = futures[future]
                try:
                    success, message = future.result()
                    if success:
                        self.log(f"✓ {message}")
                    else:
                        self.log(f"✗ {message}")
                        all_successful = False
                except Exception as e:
                    self.log(f"✗ Error downloading {filename}: {e}")
                    all_successful = False

        if all_successful:
            self.log("GeoFiles updated successfully!")
            messagebox.showinfo("Success", "GeoFiles updated successfully!")
        else:
            self.log("GeoFiles update failed. Check logs for details.")
            messagebox.showerror("Error", "Failed to update one or more GeoFiles.")

    def _download_file_segmented(self, url, filename, file_description, num_segments=4):
        try:
            head_response = requests.head(url, timeout=5)
            head_response.raise_for_status()
            total_size = int(head_response.headers.get('content-length', 0))
            if total_size == 0:
                return self._download_file_normal(url, filename, file_description)

            self.log(f"Downloading {file_description} ({total_size} bytes) with {num_segments} threads...")
            segment_size = total_size // num_segments
            segments = [(i * segment_size, (i + 1) * segment_size - 1) for i in range(num_segments)]
            segments[-1] = (segments[-1][0], total_size - 1)
            
            segment_files = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_segments) as executor:
                future_to_segment = {executor.submit(self._download_segment, url, start, end, f"{filename}.part{i}"): i for i, (start, end) in enumerate(segments)}
                for future in concurrent.futures.as_completed(future_to_segment):
                    success, part_filename = future.result()
                    if not success: raise Exception(f"Segment download failed: {part_filename}")
                    segment_files.append(part_filename)
            
            segment_files.sort()
            with open(filename, 'wb') as outfile:
                for part_filename in segment_files:
                    with open(part_filename, 'rb') as infile:
                        outfile.write(infile.read())
                    os.remove(part_filename)
            return True, f"{file_description} downloaded successfully"
        except Exception as e:
            self.log(f"Segmented download failed for {file_description}, falling back. Error: {e}")
            return self._download_file_normal(url, filename, file_description)

    def _download_segment(self, url, start, end, filename):
        try:
            headers = {'Range': f'bytes={start}-{end}'}
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            return True, filename
        except Exception as e:
            return False, str(e)

    def _download_file_normal(self, url, filename, file_description):
        try:
            self.log(f"Starting normal download of {file_description}...")
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            return True, f"{file_description} downloaded successfully"
        except Exception as e:
            return False, f"Error downloading {file_description}: {str(e)}"

def main():
    kill_xray_processes()
    root = tk.Tk()
    app = VPNConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
