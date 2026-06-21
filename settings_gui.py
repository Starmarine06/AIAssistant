import os
import json
import shutil
import time
import threading
import uuid
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Configure theme and appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SettingsGUI(ctk.CTk):
    def __init__(self, config_dir, on_save_callback=None):
        super().__init__()
        
        self.config_dir = config_dir
        self.on_save_callback = on_save_callback
        self.config_path = os.path.join(config_dir, "config.json")
        self.macros_path = os.path.join(config_dir, "macros.json")
        self.tasks_path = os.path.join(config_dir, "tasks.json")
        self.selected_creds_path = None
        
        # Window settings
        self.title("AI Assistant Control Center")
        self.geometry("750x600")
        self.resizable(False, False)
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{750}x{600}+{x}+{y}')
        
        self.setup_ui()
        self.load_existing_config()
        self.refresh_macro_list()
        self.refresh_task_list()

    def setup_ui(self):
        # Background Frame
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title Label
        title_label = ctk.CTkLabel(
            main_frame, 
            text="AI Assistant Configuration & Control Center", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(15, 10))
        
        # Tab View
        self.tabview = ctk.CTkTabview(main_frame, width=700, height=500, corner_radius=10)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.tabview.add("System Config")
        self.tabview.add("Macros & Scheduler")
        
        # --- TAB 1: System Config ---
        tab1 = self.tabview.tab("System Config")
        
        tg_label = ctk.CTkLabel(
            tab1, 
            text="Telegram Bot Token:", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        tg_label.pack(anchor="w", padx=40, pady=(15, 2))
        
        self.tg_entry = ctk.CTkEntry(
            tab1, 
            placeholder_text="Enter Telegram Bot Token (from @BotFather)",
            width=580, 
            height=35
        )
        self.tg_entry.pack(padx=40, pady=5)
        
        nv_label = ctk.CTkLabel(
            tab1, 
            text="NVIDIA API Key:", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        nv_label.pack(anchor="w", padx=40, pady=(15, 2))
        
        self.nv_entry = ctk.CTkEntry(
            tab1, 
            placeholder_text="Enter NVIDIA API Key (nvapi-...)",
            width=580, 
            height=35,
            show="*"
        )
        self.nv_entry.pack(padx=40, pady=5)
        
        gcal_label = ctk.CTkLabel(
            tab1, 
            text="Google Calendar Credentials (credentials.json):", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        gcal_label.pack(anchor="w", padx=40, pady=(15, 2))
        
        file_frame = ctk.CTkFrame(tab1, fg_color="transparent")
        file_frame.pack(fill="x", padx=40, pady=5)
        
        self.file_label = ctk.CTkLabel(
            file_frame, 
            text="No credentials file selected", 
            width=430, 
            anchor="w",
            text_color="#aaaaaa",
            fg_color="#2b2b2b",
            height=35,
            corner_radius=6
        )
        self.file_label.pack(side="left", padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            file_frame, 
            text="Browse File", 
            width=140, 
            height=35,
            command=self.browse_credentials
        )
        browse_btn.pack(side="right")
        
        btn_frame = ctk.CTkFrame(tab1, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(40, 10))
        
        self.status_label = ctk.CTkLabel(
            btn_frame, 
            text="", 
            text_color="#ff5555",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left")
        
        self.save_btn = ctk.CTkButton(
            btn_frame, 
            text="Save & Start Bot", 
            width=180, 
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.save_config
        )
        self.save_btn.pack(side="right")
        
        # --- TAB 2: Macros & Scheduler ---
        tab2 = self.tabview.tab("Macros & Scheduler")
        
        # Grid layout for Tab 2
        tab2.grid_columnconfigure(0, weight=4) # Macros
        tab2.grid_columnconfigure(1, weight=5) # Scheduler
        
        # LEFT: Macro Recording & Lists
        macro_frame = ctk.CTkFrame(tab2, corner_radius=10, fg_color="#222222")
        macro_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        macro_title = ctk.CTkLabel(macro_frame, text="Macros Recorder", font=ctk.CTkFont(size=15, weight="bold"))
        macro_title.pack(pady=10)
        
        # Scrollable Frame for Macros List
        self.macro_list_frame = ctk.CTkScrollableFrame(macro_frame, width=260, height=240, fg_color="#181818")
        self.macro_list_frame.pack(padx=10, pady=5)
        self.macro_radio_var = tk.StringVar(value="")
        
        # Macro Buttons
        m_btn_frame = ctk.CTkFrame(macro_frame, fg_color="transparent")
        m_btn_frame.pack(fill="x", padx=10, pady=10)
        
        rec_btn = ctk.CTkButton(m_btn_frame, text="🔴 Record", width=75, command=self.open_record_dialog)
        rec_btn.grid(row=0, column=0, padx=2)
        
        play_btn = ctk.CTkButton(m_btn_frame, text="▶️ Play", width=75, command=self.play_selected_macro)
        play_btn.grid(row=0, column=1, padx=2)
        
        del_btn = ctk.CTkButton(m_btn_frame, text="🗑️ Delete", width=75, fg_color="#d9534f", hover_color="#c9302c", command=self.delete_selected_macro)
        del_btn.grid(row=0, column=2, padx=2)
        
        # RIGHT: Tasks Scheduler
        scheduler_frame = ctk.CTkFrame(tab2, corner_radius=10, fg_color="#222222")
        scheduler_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        sched_title = ctk.CTkLabel(scheduler_frame, text="Task Scheduler", font=ctk.CTkFont(size=15, weight="bold"))
        sched_title.pack(pady=10)
        
        # List of Active Tasks
        self.task_list_frame = ctk.CTkScrollableFrame(scheduler_frame, width=320, height=130, fg_color="#181818")
        self.task_list_frame.pack(padx=10, pady=5)
        self.task_radio_var = tk.StringVar(value="")
        
        # Create Task Form
        form_frame = ctk.CTkFrame(scheduler_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Action selector dropdown
        act_lbl = ctk.CTkLabel(form_frame, text="Action:", font=ctk.CTkFont(size=12))
        act_lbl.grid(row=0, column=0, sticky="w", pady=2)
        
        self.action_var = tk.StringVar(value="run_macro")
        self.action_menu = ctk.CTkOptionMenu(form_frame, variable=self.action_var, values=["run_macro", "run_command", "take_screenshot", "lock_pc"], command=self.on_action_type_change, width=120)
        self.action_menu.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Macro select dropdown / Command text field (switches dynamically)
        self.target_label = ctk.CTkLabel(form_frame, text="Macro:", font=ctk.CTkFont(size=12))
        self.target_label.grid(row=1, column=0, sticky="w", pady=2)
        
        self.macro_select_var = tk.StringVar(value="")
        self.macro_select_menu = ctk.CTkOptionMenu(form_frame, variable=self.macro_select_var, values=[], width=180)
        self.macro_select_menu.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        self.command_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. ipconfig", width=180)
        
        # Schedule Type Dropdown
        type_lbl = ctk.CTkLabel(form_frame, text="Type:", font=ctk.CTkFont(size=12))
        type_lbl.grid(row=2, column=0, sticky="w", pady=2)
        
        self.sched_type_var = tk.StringVar(value="daily")
        self.sched_type_menu = ctk.CTkOptionMenu(form_frame, variable=self.sched_type_var, values=["daily", "weekly", "interval", "one_off"], command=self.on_sched_type_change, width=120)
        self.sched_type_menu.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
        # Schedule values frame
        self.value_lbl = ctk.CTkLabel(form_frame, text="Time (HH:MM):", font=ctk.CTkFont(size=12))
        self.value_lbl.grid(row=3, column=0, sticky="w", pady=2)
        
        self.time_entry = ctk.CTkEntry(form_frame, placeholder_text="14:30", width=100)
        self.time_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        
        self.day_var = tk.StringVar(value="Monday")
        self.day_menu = ctk.CTkOptionMenu(form_frame, variable=self.day_var, values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], width=100)
        
        # Sched Buttons
        s_btn_frame = ctk.CTkFrame(scheduler_frame, fg_color="transparent")
        s_btn_frame.pack(fill="x", padx=10, pady=10)
        
        add_task_btn = ctk.CTkButton(s_btn_frame, text="➕ Add Task", width=120, command=self.add_scheduled_task)
        add_task_btn.pack(side="left", padx=5)
        
        del_task_btn = ctk.CTkButton(s_btn_frame, text="🗑️ Delete Task", width=120, fg_color="#d9534f", hover_color="#c9302c", command=self.delete_selected_task)
        del_task_btn.pack(side="right", padx=5)

    # --- ACTION HANDLERS ---
    def on_action_type_change(self, val):
        if val == "run_macro":
            self.command_entry.grid_forget()
            self.target_label.configure(text="Macro:")
            self.macro_select_menu.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        elif val == "run_command":
            self.macro_select_menu.grid_forget()
            self.target_label.configure(text="Command:")
            self.command_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        else:
            self.macro_select_menu.grid_forget()
            self.command_entry.grid_forget()
            self.target_label.configure(text="No Params Needed")

    def on_sched_type_change(self, val):
        self.time_entry.grid_forget()
        self.day_menu.grid_forget()
        
        if val == "daily":
            self.value_lbl.configure(text="Time (HH:MM):")
            self.time_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        elif val == "weekly":
            self.value_lbl.configure(text="Day & Time:")
            self.day_menu.grid(row=3, column=1, padx=5, pady=2, sticky="w")
            # Reuse time entry on next row
            self.time_entry.grid(row=4, column=1, padx=5, pady=2, sticky="w")
        elif val == "interval":
            self.value_lbl.configure(text="Interval (sec):")
            self.time_entry.configure(placeholder_text="60")
            self.time_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        elif val == "one_off":
            self.value_lbl.configure(text="Delay (sec):")
            self.time_entry.configure(placeholder_text="600")
            self.time_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")

    # --- CREDENTIALS BROWSER ---
    def browse_credentials(self):
        file_path = filedialog.askopenfilename(
            title="Select credentials.json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            self.selected_creds_path = file_path
            self.file_label.configure(
                text=os.path.basename(file_path),
                text_color="#55ff55"
            )

    def load_existing_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                self.tg_entry.insert(0, data.get("telegram_token", ""))
                self.nv_entry.insert(0, data.get("nvidia_api_key", ""))
            except Exception:
                pass
        
        dest_creds = os.path.join(self.config_dir, "credentials.json")
        if os.path.exists(dest_creds):
            self.selected_creds_path = dest_creds
            self.file_label.configure(
                text="credentials.json (Imported)",
                text_color="#55ff55"
            )

    def save_config(self):
        tg_token = self.tg_entry.get().strip()
        nv_key = self.nv_entry.get().strip()
        
        if not tg_token:
            self.status_label.configure(text="❌ Telegram token is required")
            return
        if not nv_key:
            self.status_label.configure(text="❌ NVIDIA API key is required")
            return
        if not self.selected_creds_path:
            self.status_label.configure(text="❌ Google credentials.json is required")
            return
            
        os.makedirs(self.config_dir, exist_ok=True)
        dest_creds = os.path.join(self.config_dir, "credentials.json")
        if self.selected_creds_path != dest_creds:
            try:
                shutil.copy(self.selected_creds_path, dest_creds)
            except Exception as e:
                self.status_label.configure(text=f"❌ Error copying credentials: {e}")
                return
                
        config_data = {
            "telegram_token": tg_token,
            "nvidia_api_key": nv_key,
            "authorized_chat_id": None
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    old_data = json.load(f)
                if old_data.get("authorized_chat_id"):
                    config_data["authorized_chat_id"] = old_data["authorized_chat_id"]
            except Exception:
                pass
                
        try:
            with open(self.config_path, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            self.status_label.configure(text=f"❌ Error saving config: {e}")
            return
            
        self.status_label.configure(text="✅ Configuration saved!", text_color="#55ff55")
        self.update()
        self.after(1000, self.close_and_callback)

    def close_and_callback(self):
        self.destroy()
        if self.on_save_callback:
            self.on_save_callback()

    # --- MACROS BACKEND & RECORDER ---
    def refresh_macro_list(self):
        for widget in self.macro_list_frame.winfo_children():
            widget.destroy()
            
        macros = {}
        if os.path.exists(self.macros_path):
            try:
                with open(self.macros_path, "r") as f:
                    macros = json.load(f)
            except Exception:
                pass
                
        macro_names = list(macros.keys())
        self.macro_select_menu.configure(values=macro_names)
        if macro_names:
            self.macro_select_var.set(macro_names[0])
        else:
            self.macro_select_var.set("")
            
        for m_name in macro_names:
            ev_count = len(macros[m_name].get("events", []))
            rb = ctk.CTkRadioButton(
                self.macro_list_frame, 
                text=f"{m_name} ({ev_count} events)", 
                variable=self.macro_radio_var, 
                value=m_name
            )
            rb.pack(anchor="w", padx=10, pady=5)

    def open_record_dialog(self):
        dialog = ctk.CTkInputDialog(text="Enter name for new macro:", title="Create Macro")
        name = dialog.get_input()
        if not name:
            return
        name = name.strip()
        if not name:
            return
            
        RecordWindow(self, name, self.macros_path, self.refresh_macro_list)

    def play_selected_macro(self):
        m_name = self.macro_radio_var.get()
        if not m_name:
            messagebox.showwarning("Warning", "Select a macro to play!")
            return
            
        if os.path.exists(self.macros_path):
            try:
                with open(self.macros_path, "r") as f:
                    macros = json.load(f)
            except Exception:
                return
            
            macro = macros.get(m_name)
            if not macro:
                return
                
            def do_play():
                events = macro.get("events", [])
                from pynput import mouse, keyboard
                mouse_ctrl = mouse.Controller()
                keyboard_ctrl = keyboard.Controller()
                
                start_time = time.time()
                for ev in events:
                    target_time = start_time + ev["time"]
                    delay = target_time - time.time()
                    if delay > 0:
                        time.sleep(delay)
                    try:
                        ev_type = ev["type"]
                        if ev_type == "click":
                            mouse_ctrl.position = (ev["x"], ev["y"])
                            btn = getattr(mouse.Button, ev.get("button", "left").lower(), mouse.Button.left)
                            mouse_ctrl.click(btn)
                        elif ev_type in ("key_down", "key_up"):
                            kname = ev["key"]
                            kobj = getattr(keyboard.Key, kname) if hasattr(keyboard.Key, kname) else kname
                            if ev_type == "key_down":
                                keyboard_ctrl.press(kobj)
                            else:
                                keyboard_ctrl.release(kobj)
                    except Exception:
                        pass
                        
            t = threading.Thread(target=do_play, daemon=True)
            t.start()

    def delete_selected_macro(self):
        m_name = self.macro_radio_var.get()
        if not m_name:
            messagebox.showwarning("Warning", "Select a macro to delete!")
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete macro '{m_name}'?"):
            if os.path.exists(self.macros_path):
                try:
                    with open(self.macros_path, "r") as f:
                        macros = json.load(f)
                    if m_name in macros:
                        del macros[m_name]
                        with open(self.macros_path, "w") as f:
                            json.dump(macros, f, indent=4)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not delete: {e}")
                self.refresh_macro_list()

    # --- SCHEDULER BACKEND ---
    def refresh_task_list(self):
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
            
        tasks = {}
        if os.path.exists(self.tasks_path):
            try:
                with open(self.tasks_path, "r") as f:
                    tasks = json.load(f)
            except Exception:
                pass
                
        active_tasks = [t for t in tasks.values() if t.get("active", True)]
        for t in active_tasks:
            t_type = t.get("task_type")
            t_desc = ""
            if t_type == "interval":
                t_desc = f"every {t.get('interval_seconds')}s"
            elif t_type == "daily":
                t_desc = f"daily at {t.get('time_str')}"
            elif t_type == "weekly":
                t_desc = f"weekly on {t.get('day_str')} @ {t.get('time_str')}"
            else:
                t_desc = "one-off"
                
            action_desc = f"{t.get('action')}"
            if t.get("action") == "run_macro":
                action_desc += f" ({t.get('action_parameters', {}).get('macro_name', '')})"
            elif t.get("action") == "run_command":
                action_desc += f" ({t.get('action_parameters', {}).get('command', '')})"
                
            rb = ctk.CTkRadioButton(
                self.task_list_frame, 
                text=f"{t.get('name')} | {action_desc} ({t_desc})",
                variable=self.task_radio_var, 
                value=t.get("id")
            )
            rb.pack(anchor="w", padx=10, pady=4)

    def add_scheduled_task(self):
        action = self.action_var.get()
        sched_type = self.sched_type_var.get()
        
        act_params = {}
        task_name = f"GUI Task {sched_type.capitalize()}"
        if action == "run_macro":
            macro = self.macro_select_var.get()
            if not macro:
                messagebox.showerror("Error", "No macro selected!")
                return
            act_params = {"macro_name": macro}
            task_name = f"Macro: {macro}"
        elif action == "run_command":
            cmd = self.command_entry.get().strip()
            if not cmd:
                messagebox.showerror("Error", "Command field is empty!")
                return
            act_params = {"command": cmd}
            task_name = f"CMD: {cmd[:15]}..."
        
        next_run = 0.0
        time_str = "00:00"
        day_str = "Monday"
        interval_sec = 60
        
        try:
            if sched_type == "daily":
                time_str = self.time_entry.get().strip()
                if not time_str or ":" not in time_str:
                    messagebox.showerror("Error", "Enter time as HH:MM")
                    return
                now = datetime.datetime.now()
                h, m = map(int, time_str.split(":"))
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target <= now:
                    target += datetime.timedelta(days=1)
                next_run = target.timestamp()
                
            elif sched_type == "weekly":
                day_str = self.day_var.get()
                time_str = self.time_entry.get().strip()
                if not time_str or ":" not in time_str:
                    messagebox.showerror("Error", "Enter time as HH:MM")
                    return
                    
                days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                target_day_idx = days.index(day_str.lower())
                now = datetime.datetime.now()
                h, m = map(int, time_str.split(":"))
                
                curr_day_idx = now.weekday()
                days_ahead = target_day_idx - curr_day_idx
                if days_ahead < 0:
                    days_ahead += 7
                elif days_ahead == 0:
                    target_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    if target_time <= now:
                        days_ahead = 7
                target = now.replace(hour=h, minute=m, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
                next_run = target.timestamp()
                
            elif sched_type == "interval":
                interval_str = self.time_entry.get().strip()
                interval_sec = int(interval_str or 60)
                next_run = time.time() + interval_sec
                
            elif sched_type == "one_off":
                delay_str = self.time_entry.get().strip()
                interval_sec = int(delay_str or 600)
                next_run = time.time() + interval_sec
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse schedule inputs: {e}")
            return
            
        auth_chat_id = 0
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                auth_chat_id = config.get("authorized_chat_id") or 0
            except Exception:
                pass
                
        task_id = str(uuid.uuid4())[:8]
        new_task = {
            "id": task_id,
            "name": task_name,
            "task_type": sched_type,
            "interval_seconds": interval_sec if sched_type in ("interval", "one_off") else None,
            "time_str": time_str if sched_type in ("daily", "weekly") else None,
            "day_str": day_str if sched_type == "weekly" else None,
            "action": action,
            "action_parameters": act_params,
            "chat_id": auth_chat_id,
            "next_run": next_run,
            "last_run": None,
            "active": True
        }
        
        tasks = {}
        if os.path.exists(self.tasks_path):
            try:
                with open(self.tasks_path, "r") as f:
                    tasks = json.load(f)
            except Exception:
                pass
        tasks[task_id] = new_task
        
        try:
            with open(self.tasks_path, "w") as f:
                json.dump(tasks, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save task: {e}")
            return
            
        self.refresh_task_list()
        messagebox.showinfo("Success", f"Scheduled task added successfully! ID: {task_id}")

    def delete_selected_task(self):
        t_id = self.task_radio_var.get()
        if not t_id:
            messagebox.showwarning("Warning", "Select a task to delete!")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to cancel/delete this scheduled task?"):
            if os.path.exists(self.tasks_path):
                try:
                    with open(self.tasks_path, "r") as f:
                        tasks = json.load(f)
                    if t_id in tasks:
                        del tasks[t_id]
                        with open(self.tasks_path, "w") as f:
                            json.dump(tasks, f, indent=4)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete: {e}")
            self.refresh_task_list()


# --- TOP LEVEL DIALOG: ALWAYS ON TOP FLOATING RECORDER ---
class RecordWindow(ctk.CTkToplevel):
    def __init__(self, parent, macro_name, macros_path, on_finished_callback):
        super().__init__(parent)
        self.macro_name = macro_name
        self.macros_path = macros_path
        self.on_finished_callback = on_finished_callback
        
        self.title("Recording Macro...")
        self.geometry("380x180")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        py = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{px}+{py}")
        
        self.events = []
        self.start_time = None
        self.recording = False
        self.mouse_listener = None
        self.keyboard_listener = None
        
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.status_lbl = ctk.CTkLabel(
            main_frame, 
            text=f"Ready to record macro: '{macro_name}'", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_lbl.pack(pady=(15, 10))
        
        self.sub_lbl = ctk.CTkLabel(
            main_frame, 
            text="Starts capturing clicks and keyboard inputs immediately.", 
            text_color="#888888",
            font=ctk.CTkFont(size=11, slant="italic")
        )
        self.sub_lbl.pack(pady=(0, 15))
        
        self.btn = ctk.CTkButton(main_frame, text="🔴 Start Recording", fg_color="#5cb85c", hover_color="#4cae4c", command=self.toggle_recording)
        self.btn.pack(pady=5)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.btn.configure(text="⏹️ Stop Recording", fg_color="#d9534f", hover_color="#c9302c")
            self.status_lbl.configure(text="🎥 Recording in progress... Perform actions now.")
            self.sub_lbl.configure(text="Minimize this window or start clicking/typing!")
            self.start_listeners()
        else:
            self.stop_listeners()
            self.save_macro_data()
            self.destroy()

    def start_listeners(self):
        from pynput import mouse, keyboard
        self.events = []
        self.start_time = time.time()
        
        def on_click(x, y, button, pressed):
            if pressed:
                self.events.append({
                    "type": "click",
                    "x": x,
                    "y": y,
                    "button": button.name,
                    "time": time.time() - self.start_time
                })
                
        def on_press(key):
            try:
                key_str = key.char
            except AttributeError:
                key_str = key.name
            self.events.append({
                "type": "key_down",
                "key": key_str,
                "time": time.time() - self.start_time
            })
            
        def on_release(key):
            try:
                key_str = key.char
            except AttributeError:
                key_str = key.name
            self.events.append({
                "type": "key_up",
                "key": key_str,
                "time": time.time() - self.start_time
            })
            
        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_listeners(self):
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def save_macro_data(self):
        if self.events:
            for idx in range(len(self.events) - 1, -1, -1):
                if self.events[idx]["type"] == "click":
                    del self.events[idx]
                    break
                    
        macros = {}
        if os.path.exists(self.macros_path):
            try:
                with open(self.macros_path, "r") as f:
                    macros = json.load(f)
            except Exception:
                pass
                
        macros[self.macro_name] = {
            "name": self.macro_name,
            "events": self.events
        }
        
        try:
            with open(self.macros_path, "w") as f:
                json.dump(macros, f, indent=4)
            messagebox.showinfo("Success", f"Macro '{self.macro_name}' saved successfully with {len(self.events)} events!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save macro: {e}")
            
        if self.on_finished_callback:
            self.on_finished_callback()

    def on_close(self):
        self.stop_listeners()
        self.destroy()

def show_macro_recorder(config_dir):
    app = ctk.CTk()
    app.withdraw()
    
    dialog = ctk.CTkInputDialog(text="Enter name for new macro:", title="Create Macro")
    name = dialog.get_input()
    if not name or not name.strip():
        app.destroy()
        return
        
    name = name.strip()
    macros_path = os.path.join(config_dir, "macros.json")
    
    def on_finish():
        app.destroy()
        
    rec = RecordWindow(app, name, macros_path, on_finish)
    
    def on_rec_close():
        rec.on_close()
        app.destroy()
    rec.protocol("WM_DELETE_WINDOW", on_rec_close)
    
    app.mainloop()

def show_settings_gui(config_dir, on_save_callback=None):
    app = SettingsGUI(config_dir, on_save_callback)
    app.mainloop()

if __name__ == "__main__":
    test_dir = os.path.join(os.path.expanduser("~"), ".test_ai_assistant")
    os.makedirs(test_dir, exist_ok=True)
    show_settings_gui(test_dir)
