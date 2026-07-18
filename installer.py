import os
import sys
import shutil
import threading
import time
import subprocess
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

# Configure theme and appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def create_shortcut(target_path, shortcut_path, name="AI Assistant"):
    """Create a Windows or Linux shortcut depending on the operating system."""
    if sys.platform == 'win32':
        try:
            powershell_cmd = (
                f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut_path}'); "
                f"$s.TargetPath = '{target_path}'; "
                f"$s.WorkingDirectory = '{os.path.dirname(target_path)}'; "
                f"$s.Save()"
            )
            subprocess.run(["powershell", "-Command", powershell_cmd], shell=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Error creating shortcut: {e}")
            return False
    else:
        try:
            content = f"""[Desktop Entry]
Type=Application
Name={name}
Exec={target_path}
Terminal=false
Categories=Utility;
"""
            with open(shortcut_path, "w") as f:
                f.write(content)
            os.chmod(shortcut_path, 0o755)
            return True
        except Exception as e:
            print(f"Error creating shortcut: {e}")
            return False

class InstallerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Paths
        if sys.platform == 'win32':
            self.default_install_dir = os.path.join(
                os.path.expanduser("~"), "AppData", "Local", "Programs", "AIAssistant"
            )
        else:
            self.default_install_dir = os.path.join(
                os.path.expanduser("~"), ".local", "share", "AIAssistant"
            )
        self.install_dir = self.default_install_dir
        self.launch_on_startup = tk.BooleanVar(value=True)
        self.launch_now = tk.BooleanVar(value=True)
        
        # Window Configuration
        self.title("AI Assistant Installer")
        self.geometry("550x400")
        self.resizable(False, False)
        
        # Center Window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Current screen tracker
        self.current_frame = None
        self.show_welcome_screen()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    def update_status(self, text, progress=None, text_color=None):
        def update():
            self.status_label.configure(text=text)
            if progress is not None:
                self.progress_bar.set(progress)
            if text_color is not None:
                self.status_label.configure(text_color=text_color)
        self.after(0, update)

    def show_welcome_screen(self):
        self.clear_frame()
        
        self.current_frame = ctk.CTkFrame(self, corner_radius=15)
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            self.current_frame, 
            text="AI Assistant Setup", 
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title_label.pack(pady=(40, 10))
        
        desc_label = ctk.CTkLabel(
            self.current_frame, 
            text="Welcome to the AI Assistant Setup Wizard.\n\nThis installer will set up your AI Assistant Telegram Bot and PC controller on your system.",
            font=ctk.CTkFont(size=14),
            justify="center",
            wraplength=450
        )
        desc_label.pack(pady=20)
        
        # Startup Option Checkbox
        startup_text = "Start AI Assistant automatically when Windows boots" if sys.platform == 'win32' else "Start AI Assistant automatically when system boots"
        startup_cb = ctk.CTkCheckBox(
            self.current_frame, 
            text=startup_text,
            variable=self.launch_on_startup,
            font=ctk.CTkFont(size=12)
        )
        startup_cb.pack(pady=10)
        
        # Bottom Button
        next_btn = ctk.CTkButton(
            self.current_frame, 
            text="Next", 
            width=150, 
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.show_location_screen
        )
        next_btn.pack(side="bottom", pady=20)
    def show_location_screen(self):
        self.clear_frame()
        
        self.current_frame = ctk.CTkFrame(self, corner_radius=15)
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            self.current_frame, 
            text="Select Install Location", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        desc_label = ctk.CTkLabel(
            self.current_frame, 
            text="Select the destination folder where the application will be installed:",
            font=ctk.CTkFont(size=13),
            anchor="w",
            justify="left"
        )
        desc_label.pack(fill="x", padx=40, pady=(10, 5))
        
        # Directory Selection
        dir_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        dir_frame.pack(fill="x", padx=40, pady=10)
        
        self.dir_label = ctk.CTkLabel(
            dir_frame, 
            text=self.install_dir, 
            width=320, 
            anchor="w",
            fg_color="#2b2b2b",
            height=35,
            corner_radius=6
        )
        self.dir_label.pack(side="left", padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            dir_frame, 
            text="Browse...", 
            width=110, 
            height=35,
            command=self.browse_dir
        )
        browse_btn.pack(side="right")
        
        # Bottom Buttons
        btn_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=40, pady=20)
        
        back_btn = ctk.CTkButton(
            btn_frame, 
            text="Back", 
            width=100, 
            height=35,
            command=self.show_welcome_screen
        )
        back_btn.pack(side="left")
        
        install_btn = ctk.CTkButton(
            btn_frame, 
            text="Install", 
            width=150, 
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_installation
        )
        install_btn.pack(side="right")
 
    def browse_dir(self):
        chosen_dir = filedialog.askdirectory(
            title="Select Install Directory",
            initialdir=self.install_dir
        )
        if chosen_dir:
            self.install_dir = os.path.abspath(chosen_dir)
            self.dir_label.configure(text=self.install_dir)
 
    def start_installation(self):
        self.clear_frame()
        
        self.current_frame = ctk.CTkFrame(self, corner_radius=15)
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            self.current_frame, 
            text="Installing AI Assistant...", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(40, 10))
        
        self.status_label = ctk.CTkLabel(
            self.current_frame, 
            text="Preparing directories...", 
            font=ctk.CTkFont(size=13)
        )
        self.status_label.pack(pady=10)
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.current_frame, width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
        # Start installation thread
        threading.Thread(target=self.run_install, daemon=True).start()
 
    def run_install(self):
        try:
            # Terminate any running bot process to release the file lock
            try:
                if sys.platform == 'win32':
                    subprocess.run(["taskkill", "/F", "/IM", "bot.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["pkill", "-f", "bot"], capture_output=True)
            except Exception:
                pass
                
            # 1. Create directory structure
            self.update_status("Creating directories...", 0.2)
            os.makedirs(self.install_dir, exist_ok=True)
            time.sleep(0.5)
            
            # 2. Locate bundled bot and copy it
            self.update_status("Extracting application files...", 0.4)
            # If running as PyInstaller EXE, the resource is in sys._MEIPASS
            meipass = getattr(sys, '_MEIPASS', None)
            
            exe_name = "bot.exe" if sys.platform == 'win32' else "bot"
            
            if meipass:
                src_exe = os.path.join(meipass, exe_name)
            else:
                # Developer mode fallback (look in dist/ or local workspace)
                src_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", exe_name)
                if not os.path.exists(src_exe):
                    src_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name)
                    
            dest_exe = os.path.join(self.install_dir, exe_name)
            
            # Verify bot source exists before copying
            if os.path.exists(src_exe):
                shutil.copy2(src_exe, dest_exe)
            else:
                # If we're testing the installer itself without a built bot, write a dummy file
                with open(dest_exe, "w") as f:
                    f.write("DUMMY BOT CONTENT (For testing installer)")
                if sys.platform != 'win32':
                    os.chmod(dest_exe, 0o755)
            
            self.update_status("Creating desktop shortcuts...", 0.6)
            time.sleep(0.5)
            
            # 3. Create Shortcuts
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            if sys.platform == 'win32':
                desktop_shortcut = os.path.join(desktop_dir, "AI Assistant.lnk")
            else:
                desktop_shortcut = os.path.join(desktop_dir, "AIAssistant.desktop")
            create_shortcut(dest_exe, desktop_shortcut)
            
            # Start Menu / Desktop Launcher shortcut
            self.update_status("Adding to applications launcher...", 0.7)
            if sys.platform == 'win32':
                start_menu_dir = os.path.join(
                    os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs"
                )
                os.makedirs(start_menu_dir, exist_ok=True)
                start_menu_shortcut = os.path.join(start_menu_dir, "AI Assistant.lnk")
            else:
                start_menu_dir = os.path.join(
                    os.path.expanduser("~"), ".local", "share", "applications"
                )
                os.makedirs(start_menu_dir, exist_ok=True)
                start_menu_shortcut = os.path.join(start_menu_dir, "AIAssistant.desktop")
            create_shortcut(dest_exe, start_menu_shortcut)
            
            time.sleep(0.5)
            
            # 4. Handle Launch on Startup
            if self.launch_on_startup.get():
                self.update_status("Configuring startup settings...", 0.8)
                if sys.platform == 'win32':
                    startup_dir = os.path.join(
                        os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
                    )
                    os.makedirs(startup_dir, exist_ok=True)
                    startup_shortcut = os.path.join(startup_dir, "AIAssistant.lnk")
                else:
                    startup_dir = os.path.join(
                        os.path.expanduser("~"), ".config", "autostart"
                    )
                    os.makedirs(startup_dir, exist_ok=True)
                    startup_shortcut = os.path.join(startup_dir, "AIAssistant.desktop")
                create_shortcut(dest_exe, startup_shortcut)
            
            self.update_status("Installation successful!", 1.0)
            time.sleep(0.5)
            
            # Transition to finished screen in the GUI thread
            self.after(0, self.show_finished_screen)
            
        except Exception as e:
            self.update_status(f"❌ Error: {e}", text_color="#ff5555")

    def show_finished_screen(self):
        self.clear_frame()
        
        self.current_frame = ctk.CTkFrame(self, corner_radius=15)
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            self.current_frame, 
            text="Installation Completed!", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#55ff55"
        )
        title_label.pack(pady=(40, 10))
        
        desc_label = ctk.CTkLabel(
            self.current_frame, 
            text="AI Assistant has been successfully installed on your computer.\n\nShortcuts have been created on your Desktop and Start Menu.",
            font=ctk.CTkFont(size=14),
            justify="center",
            wraplength=450
        )
        desc_label.pack(pady=20)
        
        # Launch now checkbox
        launch_cb = ctk.CTkCheckBox(
            self.current_frame, 
            text="Launch AI Assistant now",
            variable=self.launch_now,
            font=ctk.CTkFont(size=13)
        )
        launch_cb.pack(pady=10)
        
        # Finish Button
        finish_btn = ctk.CTkButton(
            self.current_frame, 
            text="Finish", 
            width=150, 
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.finish_install
        )
        finish_btn.pack(side="bottom", pady=20)

    def finish_install(self):
        if self.launch_now.get():
            # Launch bot.exe in background
            dest_exe = os.path.join(self.install_dir, "bot.exe")
            if os.path.exists(dest_exe):
                try:
                    subprocess.Popen([dest_exe], cwd=self.install_dir, start_new_session=True)
                except Exception as e:
                    print(f"Error launching app: {e}")
        
        self.destroy()

if __name__ == "__main__":
    app = InstallerGUI()
    app.mainloop()
