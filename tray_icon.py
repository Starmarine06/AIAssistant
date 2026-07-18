import os
import threading
import subprocess
from PIL import Image, ImageDraw
import pystray
from settings_gui import show_settings_gui

def create_default_icon():
    """Programmatically generate a sleek default icon (64x64)."""
    # Create an image with transparent background
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a stylish rounded circle with a gradient-like blue color
    draw.ellipse([4, 4, 60, 60], fill=(30, 144, 255, 255), outline=(255, 255, 255, 255), width=2)
    
    # Draw a stylized letter 'A' in the center
    # Using basic line drawing to ensure it works without custom fonts
    # Left leg
    draw.line([22, 45, 32, 18], fill=(255, 255, 255, 255), width=4)
    # Right leg
    draw.line([42, 45, 32, 18], fill=(255, 255, 255, 255), width=4)
    # Crossbar
    draw.line([26, 36, 38, 36], fill=(255, 255, 255, 255), width=3)
    
    return image

class BotTrayIcon:
    def __init__(self, config_dir, stop_callback=None, restart_callback=None):
        self.config_dir = config_dir
        self.stop_callback = stop_callback
        self.restart_callback = restart_callback
        self.icon = None
        self.running_gui = False
        
        self.log_path = os.path.join(config_dir, "bot.log")
        self.icon_path = os.path.join(config_dir, "app_icon.ico")

    def open_path(self, path):
        import sys
        if sys.platform == 'win32':
            os.startfile(path)
        else:
            import subprocess
            if sys.platform == 'darwin':
                subprocess.Popen(['open', path], stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(['xdg-open', path], stderr=subprocess.DEVNULL)

    def open_logs(self):
        if not os.path.exists(self.log_path):
            # Create empty log if doesn't exist
            with open(self.log_path, "w") as f:
                f.write("AI Assistant Log File\n====================\n")
        self.open_path(self.log_path)

    def open_data_dir(self):
        if os.path.exists(self.config_dir):
            self.open_path(self.config_dir)

    def launch_settings(self):
        if self.running_gui:
            return
        
        self.running_gui = True
        def run_gui():
            try:
                show_settings_gui(self.config_dir, on_save_callback=self.settings_saved)
            finally:
                self.running_gui = False
                
        # Run GUI in a separate thread so it doesn't block the tray icon menu thread
        t = threading.Thread(target=run_gui, daemon=True)
        t.start()

    def launch_macro_recorder(self):
        if self.running_gui:
            return
            
        self.running_gui = True
        def run_recorder():
            try:
                from settings_gui import show_macro_recorder
                show_macro_recorder(self.config_dir)
            finally:
                self.running_gui = False
                
        t = threading.Thread(target=run_recorder, daemon=True)
        t.start()

    def settings_saved(self):
        # Trigger reload of the bot configuration
        if self.restart_callback:
            self.restart_callback()

    def exit_action(self):
        # Stop the bot if it is running
        if self.stop_callback:
            self.stop_callback()
        # Stop the tray icon
        if self.icon:
            self.icon.stop()

    def run(self):
        # Load icon image
        if os.path.exists(self.icon_path):
            try:
                icon_image = Image.open(self.icon_path)
            except Exception:
                icon_image = create_default_icon()
        else:
            icon_image = create_default_icon()

        # Build menu
        menu = pystray.Menu(
            pystray.MenuItem("AI Assistant Bot", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Configure Settings", lambda: self.launch_settings()),
            pystray.MenuItem("Record Macro", lambda: self.launch_macro_recorder()),
            pystray.MenuItem("Open Data Folder", lambda: self.open_data_dir()),
            pystray.MenuItem("View Log File", lambda: self.open_logs()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Bot", lambda: self.exit_action())
        )

        self.icon = pystray.Icon(
            "AIAssistant",
            icon_image,
            title="AI Assistant Telegram Bot",
            menu=menu
        )
        
        # Start tray icon loop (blocking)
        self.icon.run()

if __name__ == "__main__":
    # Test tray icon
    import time
    print("Starting tray icon test. Look at your Windows tray!")
    config_dir = os.path.join(os.path.expanduser("~"), ".test_ai_assistant")
    os.makedirs(config_dir, exist_ok=True)
    tray = BotTrayIcon(config_dir, stop_callback=lambda: print("Stopping bot..."))
    tray.run()
