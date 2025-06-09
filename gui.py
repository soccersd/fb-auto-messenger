import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime
import threading
import time
import queue
import subprocess
import sys

class FacebookAutoSendGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Auto Send Message")
        self.root.geometry("1000x600")  # ลดขนาดหน้าต่างลง
        
        # Set theme colors
        self.bg_color = "#f0f2f5"
        self.primary_color = "#1877f2"
        self.text_color = "#1c1e21"
        self.button_font = ("Helvetica", 12, "bold")
        
        self.root.configure(bg=self.bg_color)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")  # ลด padding ลง
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create and configure style
        self.style = ttk.Style()
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", 
                           background=self.bg_color,
                           foreground=self.text_color,
                           font=("Helvetica", 10))
        
        # Queue for receiving log from other thread
        self.log_queue = queue.Queue()
        # Timer for checking queue and updating log
        self.root.after(100, self.process_log_queue)
        
        # Create widgets
        self.create_widgets()
        
        # Initialize variables
        self.is_running = False
        self.bot_process = None  # add process variable
        
    def create_widgets(self):
        # Title
        title_label = ttk.Label(self.main_frame, 
                              text="Facebook Auto Send Message",
                              font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # create main frame for 2 parts
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # left frame for settings
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(left_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=10)
        
        # Thread ID input
        thread_frame = ttk.Frame(config_frame)
        thread_frame.pack(fill=tk.X, pady=5)
        ttk.Label(thread_frame, text="Thread ID:").pack(side=tk.LEFT)
        self.thread_id_var = tk.StringVar()
        self.thread_id_entry = ttk.Entry(thread_frame, textvariable=self.thread_id_var, width=30)
        self.thread_id_entry.pack(side=tk.LEFT, padx=5)
        
        # Instances input
        instances_frame = ttk.Frame(config_frame)
        instances_frame.pack(fill=tk.X, pady=5)
        ttk.Label(instances_frame, text="Instances:").pack(side=tk.LEFT)
        self.instances_var = tk.StringVar()
        self.instances_entry = ttk.Entry(instances_frame, textvariable=self.instances_var, width=10)
        self.instances_entry.pack(side=tk.LEFT, padx=5)
        
        # Message input
        ttk.Label(config_frame, text="Message:").pack(anchor=tk.W)
        self.message_text = scrolledtext.ScrolledText(config_frame, height=4)
        self.message_text.pack(fill=tk.X, pady=5)
        
        # Messages Per Second input
        mps_frame = ttk.Frame(config_frame)
        mps_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mps_frame, text="Messages Per Second:").pack(side=tk.LEFT)
        self.mps_var = tk.StringVar()
        self.mps_entry = ttk.Entry(mps_frame, textvariable=self.mps_var, width=10)
        self.mps_entry.pack(side=tk.LEFT, padx=5)
        
        # Cookies input
        cookies_frame = ttk.LabelFrame(config_frame, text="Cookies", padding="10")
        cookies_frame.pack(fill=tk.X, pady=5)
        
        # c_user input
        c_user_frame = ttk.Frame(cookies_frame)
        c_user_frame.pack(fill=tk.X, pady=5)
        ttk.Label(c_user_frame, text="c_user:").pack(side=tk.LEFT)
        self.c_user_var = tk.StringVar()
        self.c_user_entry = ttk.Entry(c_user_frame, textvariable=self.c_user_var, width=50)
        self.c_user_entry.pack(side=tk.LEFT, padx=5)
        
        # xs input
        xs_frame = ttk.Frame(cookies_frame)
        xs_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xs_frame, text="xs:").pack(side=tk.LEFT)
        self.xs_var = tk.StringVar()
        self.xs_entry = ttk.Entry(xs_frame, textvariable=self.xs_var, width=50)
        self.xs_entry.pack(side=tk.LEFT, padx=5)
        
        # fr input
        fr_frame = ttk.Frame(cookies_frame)
        fr_frame.pack(fill=tk.X, pady=5)
        ttk.Label(fr_frame, text="fr:").pack(side=tk.LEFT)
        self.fr_var = tk.StringVar()
        self.fr_entry = ttk.Entry(fr_frame, textvariable=self.fr_var, width=50)
        self.fr_entry.pack(side=tk.LEFT, padx=5)
        
        # Control Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        # Create Start Button
        self.start_button = tk.Button(
            button_frame,
            text="START",
            command=self.start_sending,
            bg="#28a745",
            fg="white",
            font=self.button_font,
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3
        )
        self.start_button.pack(side=tk.LEFT, padx=20)
        
        # Create Stop Button
        self.stop_button = tk.Button(
            button_frame,
            text="STOP",
            command=self.stop_sending,
            bg="#dc3545",
            fg="white",
            font=self.button_font,
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=20)
        
        # right frame for log
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Log Frame
        log_frame = ttk.LabelFrame(right_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # create frame for log control buttons
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # clear log button
        clear_log_button = ttk.Button(
            log_control_frame,
            text="Clear Log",
            command=self.clear_log,
            style="Accent.TButton"
        )
        clear_log_button.pack(side=tk.LEFT, padx=5)
        
        # ปุ่ม Save Log
        save_log_button = ttk.Button(
            log_control_frame,
            text="Save Log",
            command=self.save_log,
            style="Accent.TButton"
        )
        save_log_button.pack(side=tk.LEFT, padx=5)
        
        # create log text widget with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # create scrollbar
        log_scrollbar = ttk.Scrollbar(log_container)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # create log text widget
        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=10,
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Consolas", 10),
            yscrollcommand=log_scrollbar.set
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # connect scrollbar to text widget
        log_scrollbar.config(command=self.log_text.yview)
        
        # set tag for text color
        self.log_text.tag_configure("error", foreground="#ff6b6b")
        self.log_text.tag_configure("success", foreground="#51cf66")
        self.log_text.tag_configure("info", foreground="#339af0")
        self.log_text.tag_configure("warning", foreground="#ffd43b")
        
        # show initial message in log
        self.log_status("=== Facebook Auto Send Message ===", "info")
        self.log_status("กรุณากรอกข้อมูลและกดปุ่ม START เพื่อเริ่มส่งข้อความ", "info")
        self.log_status("สถานะการทำงานจะแสดงที่นี่", "info")
        self.log_status("=================================", "info")
        
    def save_config(self, config, cookies):
        # save config.json (or bot_config.json)
        # use bot_config.json to separate from old config.json
        with open('bot_config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
        # save cookies.json
        # create sessions folder if not exists
        os.makedirs('sessions', exist_ok=True)
        
        with open('sessions/cookies.json', 'w') as f:
            json.dump(cookies, f, indent=4)
            
    def log_status(self, message, level="info"):
        """Add message to log with level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Add message to queue with tag
        self.log_queue.put((log_message, level))
        
    def process_log_queue(self):
        # Read message from queue and update GUI
        while not self.log_queue.empty():
            try:
                message, level = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message, level)
                self.log_text.see(tk.END)  # Scroll to the latest message
            except queue.Empty:
                pass
        # Set timer to run again in 100 milliseconds
        if self.is_running or not self.log_queue.empty():
            self.root.after(100, self.process_log_queue)
        
    def run_bot(self, config, cookies):
        self.log_status("Attempting to start bot.js...", "info")
        try:
            # Check if Node.js can run
            try:
                subprocess.run(['node', '-v'], check=True, capture_output=True, text=True, timeout=5)
                self.log_status("Node.js found.", "success")
            except FileNotFoundError:
                self.log_status("Error: Node.js command not found. Please ensure Node.js is installed and in your system's PATH.", "error")
                self.root.after(0, self.stop_sending)
                return
            except subprocess.CalledProcessError as e:
                 self.log_status(f"Error checking Node.js version: {e.stderr.strip()}", "error")
                 self.root.after(0, self.stop_sending)
                 return
            except subprocess.TimeoutExpired:
                 self.log_status("Error: Node.js version check timed out.", "error")
                 self.root.after(0, self.stop_sending)
                 return
            except Exception as e:
                 self.log_status(f"Unexpected error checking Node.js: {str(e)}", "error")
                 self.root.after(0, self.stop_sending)
                 return
            # Run bot.js with Node.js
            # Use creationflags=subprocess.CREATE_NO_WINDOW in Windows to prevent opening a new console window
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NO_WINDOW
            self.bot_process = subprocess.Popen(
                ['node', 'bot.js'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=creationflags
            )
            self.log_status("bot.js process started.", "success")
            # Read output from bot.js in this thread
            for line in iter(self.bot_process.stdout.readline, ''):
                if not self.is_running: # Check status of the process here
                    break
                if line:
                    self.log_queue.put((f"[BOT] {line.strip()}\n", "info")) # Add [BOT] tag and send to queue
            # Wait for process to finish and read remaining stderr
            stderr_output = self.bot_process.stderr.read()
            # Wait for process to finish truly
            self.bot_process.wait()
            self.log_status(f"bot.js process finished with return code {self.bot_process.returncode}.", "info")
            # Show error if any
            if self.bot_process.returncode != 0:
                if stderr_output:
                    self.log_status(f"Error from bot.js:\n{stderr_output.strip()}", "error")
                else:
                    self.log_status("bot.js finished with error but no stderr output.", "warning")
            # Call stop_sending in main thread when bot finishes
            self.root.after(0, self.stop_sending)
        except FileNotFoundError:
             # This error should be caught by checking Node.js above, but there might be other cases
             self.log_status("Error: Could not start bot.js process. Check if Node.js and bot.js exist.", "error")
             self.root.after(0, self.stop_sending)
        except Exception as e:
            self.log_status(f"Unexpected error during bot execution: {str(e)}", "error")
            self.root.after(0, self.stop_sending)
            
    def start_sending(self):
        if not self.message_text.get("1.0", tk.END).strip():
            messagebox.showerror("Error", "Please enter a message")
            return
            
        if not self.thread_id_var.get().strip():
            messagebox.showerror("Error", "Please enter Thread ID")
            return
            
        if not self.c_user_var.get().strip() or not self.xs_var.get().strip() or not self.fr_var.get().strip():
            messagebox.showerror("Error", "Please enter all cookies (c_user, xs, fr)")
            return
            
        try:
            mps = int(self.mps_var.get())
            instances = int(self.instances_var.get())
            if mps < 1 or instances < 1:
                raise ValueError
            # Calculate delay to use in config
            delay_ms = 1000 // mps
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for messages per second and instances")
            return
            
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Create config and cookies object from the values entered
        config = {
            "message": self.message_text.get("1.0", tk.END).strip(),
            "delay": delay_ms,  # Use calculated delay_ms
            "instances": instances,
            "threadId": self.thread_id_var.get(),
            "messagesPerSecond": mps # Add messagesPerSecond back into config for log in bot.js
        }
        
        cookies = [
            {
                "domain": ".facebook.com",
                "name": "c_user",
                "value": self.c_user_var.get()
            },
            {
                "domain": ".facebook.com",
                "name": "xs",
                "value": self.xs_var.get()
            },
            {
                "domain": ".facebook.com",
                "name": "fr",
                "value": self.fr_var.get()
            }
        ]
        
        # Save config and cookies to files
        self.save_config(config, cookies)
        self.log_status("Configuration and cookies saved to files.", "success")
        
        # Run bot.js in a separate thread to prevent GUI from freezing
        self.bot_thread = threading.Thread(target=self.run_bot, args=(config, cookies))
        self.bot_thread.daemon = True # Make thread end when main program ends
        self.bot_thread.start()
        
    def stop_sending(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_status("Stopping bot...", "info")
        
        # Terminate bot process if it exists
        if self.bot_process:
            try:
                if sys.platform == 'win32':
                    # Windows: Use taskkill to kill process and child processes
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.bot_process.pid)], 
                                 capture_output=True, text=True)
                else:
                    # Unix-like: Use SIGTERM
                    self.bot_process.terminate()
                    self.bot_process.wait(timeout=5)  # Wait for process to finish within 5 seconds
            except Exception as e:
                self.log_status(f"Error stopping bot process: {str(e)}", "error")
            finally:
                self.bot_process = None
        
        self.log_status("Bot stopped", "info")

    def clear_log(self):
        """Clear log text"""
        self.log_text.delete(1.0, tk.END)
        self.log_status("Log cleared", "info")
        
    def save_log(self):
        """Save log to file"""
        try:
            # Create filename from current time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"log_{timestamp}.txt"
            
            # Write log to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            
            self.log_status(f"Log saved to {filename}", "success")
        except Exception as e:
            self.log_status(f"Error saving log: {str(e)}", "error")

if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookAutoSendGUI(root)
    root.mainloop() 