import datetime
import json
import math
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


APP_DIRECTORY = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
SETTINGS_FILE = APP_DIRECTORY / "settings.json"
PRESETS = (15, 30, 45, 60, 75, 90, 105, 120)
LIGHT_THEME = dict(window="#f5f6f5", surface="#ffffff", text="#18211e",
                   muted="#53615b", border="#b7c5bd", accent="#116650",
                   accent_text="#ffffff", selected="#d9f3e6")
DARK_THEME = dict(window="#141817", surface="#222a26", text="#f2f7f4",
                  muted="#b7c6bd", border="#64776b", accent="#a6edbc",
                  accent_text="#102319", selected="#345442")


def valid_minutes_input(value):
    return not value or (value.isascii() and value.isdigit() and len(value) <= 7)


def parse_minutes(value):
    if not value or not valid_minutes_input(value) or int(value) < 1:
        raise ValueError("Enter 1 to 9,999,999 minutes.")
    return int(value)


def format_remaining(seconds):
    minutes, seconds = divmod(max(0, math.ceil(seconds)), 60)
    return f"{minutes:,}:{seconds:02d}"


def load_settings():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        theme = data.get("theme", "system") if isinstance(data, dict) else "system"
        return {"theme": theme if theme in ("system", "light", "dark") else "system"}
    except (OSError, ValueError):
        return {"theme": "system"}


def save_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def system_prefers_dark_theme():
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
    except OSError:
        return False


def set_windows_dark_title_bar(window, enabled):
    if sys.platform != "win32":
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(int(enabled))
        for attribute in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            ) == 0:
                break
    except (AttributeError, OSError):
        pass


class SleepTimerApp:
    def __init__(self, root):
        self.root = root
        self.version = "1.1.2"
        root.title("Sleep Timer")
        root.geometry("400x520")
        root.minsize(380, 520)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.settings = load_settings()
        self.theme_var = tk.StringVar(value=self.settings["theme"])
        self.minutes_var = tk.StringVar(value="30")
        self.running = False
        self.sleeping = False
        self.tick_id = None
        self.events = queue.Queue()
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.shell = tk.Frame(root)
        self.shell.pack(fill="both", expand=True, padx=24, pady=20)
        header = tk.Frame(self.shell)
        header.pack(fill="x")
        self.heading = tk.Label(header, text="Sleep Timer", font=("Segoe UI", 18, "bold"))
        self.heading.pack(side="left")
        self.theme_menu = ttk.Combobox(header, textvariable=self.theme_var,
                                      values=("system", "light", "dark"), width=7,
                                      state="readonly", font=("Segoe UI", 11))
        self.theme_menu.pack(side="right")
        self.theme_menu.bind("<<ComboboxSelected>>", self._handle_theme_changed)
        self.countdown = tk.Label(self.shell, text="30:00", font=("Segoe UI", 42, "bold"))
        self.countdown.pack(fill="x", pady=(18, 0))
        self.schedule = tk.Label(self.shell, text="Ready", font=("Segoe UI", 11))
        self.schedule.pack(fill="x", pady=(0, 12))
        self.progress = ttk.Progressbar(self.shell, maximum=1, value=0)
        self.progress.pack(fill="x", pady=(0, 14))
        self.presets = tk.Frame(self.shell)
        self.presets.pack(fill="x")
        self.preset_buttons = []
        for column in range(4):
            self.presets.columnconfigure(column, weight=1, uniform="presets")
        for index, minutes in enumerate(PRESETS):
            button = tk.Button(self.presets, text=str(minutes), font=("Segoe UI", 20, "bold"),
                               command=lambda m=minutes: self.select_preset(m),
                               relief="flat", borderwidth=0, pady=7, cursor="hand2")
            button.grid(row=index // 4, column=index % 4, sticky="ew", padx=3, pady=3)
            self.preset_buttons.append(button)
        self.input_label = tk.Label(self.shell, text="Minutes", font=("Segoe UI", 12, "bold"), anchor="w")
        self.input_label.pack(fill="x", pady=(12, 5))
        self.custom_entry = tk.Entry(self.shell, textvariable=self.minutes_var,
                                     font=("Segoe UI", 28, "bold"), justify="center",
                                     relief="flat", highlightthickness=2,
                                     validate="key", validatecommand=(root.register(valid_minutes_input), "%P"))
        self.custom_entry.pack(fill="x", ipady=6)
        self.actions = tk.Frame(self.shell)
        self.actions.pack(fill="x", pady=(16, 0))
        self.start_button = tk.Button(self.actions, text="Start timer", command=self.start_countdown,
                                      font=("Segoe UI", 13, "bold"), relief="flat", pady=11, cursor="hand2")
        self.start_button.pack(side="left", fill="x", expand=True)
        self.abort_button = tk.Button(self.actions, text="Cancel", command=self.abort_countdown,
                                      font=("Segoe UI", 13), relief="flat", pady=11, padx=18,
                                      state="disabled", cursor="hand2")
        self.abort_button.pack(side="right", padx=(8, 0))
        self.status = tk.Label(self.shell, text="", font=("Segoe UI", 10), wraplength=330)
        self.status.pack(fill="x", pady=(10, 0))
        self.minutes_var.trace_add("write", self._preview)
        root.bind("<Return>", lambda event: self.start_countdown())
        root.bind("<Escape>", lambda event: self.abort_countdown() if self.running else None)
        self.apply_theme()
        self._preview()
        root.update_idletasks()
        height = max(520, root.winfo_reqheight())
        root.geometry(f"400x{height}")
        root.minsize(380, height)
        self.poll_id = root.after(100, self._poll_sleep)

    def select_preset(self, minutes):
        self.minutes_var.set(str(minutes))

    def _preview(self, *_args):
        if self.running or self.sleeping:
            return
        try:
            minutes = parse_minutes(self.minutes_var.get())
            self._set_countdown(minutes * 60)
            when = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            self.schedule.config(text="Sleep at " + when.strftime("%d %b, %H:%M"))
            self.start_button.config(state="normal")
        except ValueError:
            self.countdown.config(text="--:--")
            self.schedule.config(text="Enter a positive number of minutes")
            self.start_button.config(state="disabled")
        self._style_presets()

    def _set_countdown(self, seconds):
        text = format_remaining(seconds)
        size = 42 if len(text) <= 7 else 28 if len(text) <= 10 else 22
        self.countdown.config(text=text, font=("Segoe UI", size, "bold"))

    def start_countdown(self):
        if self.running or self.sleeping:
            return
        try:
            minutes = parse_minutes(self.minutes_var.get())
        except ValueError as error:
            self.status.config(text=str(error))
            return
        self.total_seconds = minutes * 60
        self.deadline = time.monotonic() + self.total_seconds
        self.running = True
        self.status.config(text="Timer running")
        self.start_button.config(state="disabled")
        self.abort_button.config(state="normal")
        self.custom_entry.config(state="disabled")
        for button in self.preset_buttons:
            button.config(state="disabled")
        self._tick()

    def _tick(self):
        self.tick_id = None
        if not self.running:
            return
        remaining = self.deadline - time.monotonic()
        self._set_countdown(remaining)
        self.progress["value"] = min(1, max(0, 1 - remaining / self.total_seconds))
        if remaining <= 0:
            self.running = False
            self.sleeping = True
            self.abort_button.config(state="disabled")
            self.status.config(text="Putting Windows to sleep...")
            threading.Thread(target=self._suspend, daemon=True).start()
        else:
            self.tick_id = self.root.after(200, self._tick)

    def _suspend(self):
        started = time.monotonic()
        try:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
            self.events.put((True, (time.monotonic() - started) / 60))
        except (OSError, subprocess.CalledProcessError) as error:
            self.events.put((False, str(error)))

    def _poll_sleep(self):
        try:
            success, result = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.sleeping = False
            self._reset_controls()
            self.status.config(text=f"Welcome back. Sleep call lasted about {result:.1f} min."
                               if success else "Windows sleep failed. Please try again.")
        self.poll_id = self.root.after(100, self._poll_sleep)

    def _reset_controls(self):
        self.custom_entry.config(state="normal")
        self.abort_button.config(state="disabled")
        for button in self.preset_buttons:
            button.config(state="normal")
        self.progress["value"] = 0
        self._preview()

    def abort_countdown(self):
        if not self.running:
            return
        self.running = False
        if self.tick_id:
            self.root.after_cancel(self.tick_id)
            self.tick_id = None
        self._reset_controls()
        self.status.config(text="Timer cancelled")

    def close(self):
        if self.running and not messagebox.askyesno("Cancel timer?", "Close Sleep Timer and cancel the running timer?"):
            return
        self.abort_countdown()
        self.root.after_cancel(self.poll_id)
        self.root.destroy()

    def _handle_theme_changed(self, *_args):
        self.settings["theme"] = self.theme_var.get()
        try:
            save_settings(self.settings)
        except OSError:
            self.status.config(text="Theme applied; settings could not be saved.")
        self.apply_theme()

    def _style_presets(self):
        c = self.theme
        for minutes, button in zip(PRESETS, self.preset_buttons):
            selected = self.minutes_var.get() == str(minutes)
            button.config(bg=c["selected"] if selected else c["surface"], fg=c["text"],
                          activebackground=c["selected"], activeforeground=c["text"],
                          disabledforeground=c["muted"], highlightbackground=c["border"],
                          highlightcolor=c["accent"], highlightthickness=1)

    def apply_theme(self):
        dark = self.theme_var.get() == "dark" or (self.theme_var.get() == "system" and system_prefers_dark_theme())
        self.theme = DARK_THEME if dark else LIGHT_THEME
        c = self.theme
        for widget in (self.root, self.shell, self.presets, self.actions, self.heading.master):
            widget.config(bg=c["window"])
        for label in (self.heading, self.countdown, self.schedule, self.input_label, self.status):
            label.config(bg=c["window"], fg=c["muted"] if label in (self.schedule, self.status) else c["text"])
        self.custom_entry.config(bg=c["surface"], fg=c["text"], insertbackground=c["text"],
                                 disabledbackground=c["surface"], disabledforeground=c["muted"],
                                 highlightbackground=c["border"], highlightcolor=c["accent"],
                                 selectbackground=c["selected"], selectforeground=c["text"])
        self.start_button.config(bg=c["accent"], fg=c["accent_text"], activebackground=c["selected"],
                                 activeforeground=c["text"], disabledforeground=c["muted"])
        self.abort_button.config(bg=c["surface"], fg=c["text"], activebackground=c["selected"],
                                 activeforeground=c["text"], disabledforeground=c["muted"])
        self.style.configure("TCombobox", fieldbackground=c["surface"], background=c["surface"],
                             foreground=c["text"], arrowcolor=c["text"], bordercolor=c["border"])
        self.style.map("TCombobox", fieldbackground=[("readonly", c["surface"])],
                       foreground=[("readonly", c["text"])])
        self.style.configure("Horizontal.TProgressbar", background=c["accent"], troughcolor=c["surface"],
                             borderwidth=0, thickness=4)
        self._style_presets()
        set_windows_dark_title_bar(self.root, dark)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Windows Sleep Timer")
    parser.add_argument("--preview", choices=("light", "dark"), help="Safe preview: sleep is disabled")
    parser.add_argument("--auto-close-ms", type=int, default=0, help="Close safe preview automatically")
    options = parser.parse_args()
    if options.auto_close_ms and not options.preview:
        parser.error("--auto-close-ms requires --preview")
    root = tk.Tk()
    app = SleepTimerApp(root)
    if options.preview:
        root.title("Sleep Timer Preview - " + options.preview)
        app.theme_var.set(options.preview)
        app.apply_theme()
        app._suspend = lambda: app.events.put((False, "Preview mode"))
        app.start_button.config(command=lambda: None)
        root.unbind("<Return>")
        if options.auto_close_ms > 0:
            root.after(options.auto_close_ms, app.close)
    root.mainloop()
