import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Menu
from threading import Thread
from queue import Queue

# Constants
BASH_PATH = r"C:\Program Files\Git\bin\bash.exe"  

# GUI Colors
BG_COLOR = "#2e2e2e"
FG_COLOR = "#e6e6e6"
ENTRY_BG = "#3c3f41"
BTN_BG = "#5c5f63"
BTN_FG = "#ffffff"
OUTPUT_BG = "#1e1e1e"
ERROR_COLOR = "#ff6b6b"
COMMAND_COLOR = "#569cd6"

class ShellGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IIUI Command Shell")
        self.geometry("800x600")
        self.configure(bg=BG_COLOR)
        
        
        # Setup styles
        self.setup_styles()
        
        # Create widgets
        self.create_widgets()
        
        # Command history
        self.command_history = []
        self.history_index = -1
        
        # Start command processing
        self.command_queue = Queue()
        self.process_commands()
        
        # Welcome message
        self.display_output(
            "IIUI Command Shell \n"
            "Type commands in the entry box below\n"
            
        )
        
    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        self.style.configure("TEntry",
                            foreground=FG_COLOR,
                            fieldbackground=ENTRY_BG,
                            background=ENTRY_BG,
                            padding=6,
                            borderwidth=0)
        
        self.style.configure("TButton",
                            background=BTN_BG,
                            foreground=BTN_FG,
                            padding=8,
                            relief="flat",
                            font=('Segoe UI', 10, 'bold'))
        
        self.style.map("TButton",
                      background=[('active', '#787b7f')])
        
        self.style.configure("TFrame", background=BG_COLOR)
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, font=("Consolas", 11),
            bg=OUTPUT_BG, fg=FG_COLOR, insertbackground=FG_COLOR
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.output_text.configure(state='disabled')
        
        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Command entry
        self.entry = ttk.Entry(input_frame, style="TEntry", font=("Consolas", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self.run_command())
        self.entry.bind("<Up>", self.history_up)
        self.entry.bind("<Down>", self.history_down)
        

        # Menu
        self.create_menu()
        
    def create_menu(self):
        menubar = Menu(self)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Clear Screen", command=self.clear_screen)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)
    
    def run_command(self):
        command = self.entry.get().strip()
        if not command:
            return
        
        # Add to history
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Display command
        self.display_output(f"> {command}\n", "command")
        
        # Process command in a separate thread
        Thread(target=self.process_command, args=(command,), daemon=True).start()
        
        # Clear entry
        self.entry.delete(0, tk.END)
    
    def process_command(self, command):
        try:
            if command == "exit":
                self.quit()
                
            elif command == "pwd":
                self.command_queue.put(("output", os.getcwd()))
                
            elif command.startswith("cd "):
                path = command[3:].strip('"')
                try:
                    os.chdir(path)
                    self.command_queue.put(("output", f"Changed directory to {os.getcwd()}"))
                except FileNotFoundError:
                    self.command_queue.put(("error", "Directory not found"))
                    
            elif command.startswith("echo "):
                self.command_queue.put(("output", command[5:].strip('"')))
                
            elif command == "about":
                self.command_queue.put(("output", "This is a custom shell made by F22-B students"))
                
            elif command == "ls":
                self.run_system_command("dir")
                
            elif command == "ls -a":
                self.run_system_command("dir /a")
                
            elif command == "date":
                self.run_system_command("date /T")
                
            elif command == "clear":
                self.command_queue.put(("clear", ""))
                
            elif command == "fork":
                self.run_python_script("L1_task1.py")
                
            elif command.startswith("bash "):
                self.run_bash_command(command[5:])
                
            else:
                self.run_system_command(command)
                
        except Exception as e:
            self.command_queue.put(("error", f"Error: {e}"))
    
    def run_system_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output = result.stdout if result.stdout else result.stderr
            if result.returncode != 0:
                self.command_queue.put(("error", output))
            else:
                self.command_queue.put(("output", output))
        except Exception as e:
            self.command_queue.put(("error", f"Error running command: {e}"))
    
    def run_bash_command(self, command):
        try:
            result = subprocess.run([BASH_PATH, "-c", command], 
                                  capture_output=True, text=True)
            output = result.stdout if result.stdout else result.stderr
            if result.returncode != 0:
                self.command_queue.put(("error", output))
            else:
                self.command_queue.put(("output", output))
        except Exception as e:
            self.command_queue.put(("error", f"Error running bash command: {e}"))
    
    def run_python_script(self, script_name):
        try:
            self.command_queue.put(("output", "Creating child process..."))
            
            def run_script():
                try:
                    child = subprocess.Popen(
                        [sys.executable, script_name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1
                    )
                    
                    # Stream output in real-time
                    for line in child.stdout:
                        self.command_queue.put(("output", line))
                    for line in child.stderr:
                        self.command_queue.put(("error", line))
                    
                    return_code = child.wait()
                    self.command_queue.put(("output", 
                        f"\nProcess finished with return code: {return_code}"))
                except Exception as e:
                    self.command_queue.put(("error", f"Error: {e}"))
            
            Thread(target=run_script, daemon=True).start()
        except Exception as e:
            self.command_queue.put(("error", f"Error creating process: {e}"))
    
    def process_commands(self):
        """Process commands from the queue in the main thread"""
        while not self.command_queue.empty():
            cmd_type, output = self.command_queue.get()
            
            if cmd_type == "clear":
                self.clear_screen()
            elif cmd_type == "error":
                self.display_output(f"{output}\n", "error")
            else:
                self.display_output(f"{output}\n", "output")
        
        self.after(100, self.process_commands)
    
    def display_output(self, text, text_type="output"):
        self.output_text.configure(state='normal')
        
        if text_type == "command":
            self.output_text.insert(tk.END, text, "command")
        elif text_type == "error":
            self.output_text.insert(tk.END, text, "error")
        else:
            self.output_text.insert(tk.END, text, "output")
        
        self.output_text.configure(state='disabled')
        self.output_text.see(tk.END)
    
    def clear_screen(self):
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
    
    def history_up(self, event):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.command_history[self.history_index])
    
    def history_down(self, event):
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.command_history[self.history_index])
        elif self.command_history and self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
    
    def show_about(self):
        messagebox.showinfo(
            "About IIUI Command Shell",
            "This is a custom shell made by F22-B students\n"

        )

if __name__ == "__main__":
    app = ShellGUI()
    
    # Configure text tags for colored output
    app.output_text.tag_config("command", foreground=COMMAND_COLOR)
    app.output_text.tag_config("output", foreground=FG_COLOR)
    app.output_text.tag_config("error", foreground=ERROR_COLOR)
    
    app.mainloop()