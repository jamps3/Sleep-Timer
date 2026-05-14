import datetime
import json
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


LIGHT_THEME = {
    "window": "#f5f7fb",
    "surface": "#ffffff",
    "surface_alt": "#eef2f7",
    "border": "#cfd7e3",
    "text": "#1f2933",
    "muted": "#52616f",
    "accent": "#2563eb",
    "accent_text": "#ffffff",
    "button": "#e6edf7",
    "button_active": "#d6e2f2",
    "entry": "#ffffff",
    "entry_text": "#111827",
    "select": "#cfe0ff",
    "select_text": "#0f172a",
    "drop": "#f4f7fb",
}
DARK_THEME = {
    "window": "#111827",
    "surface": "#1f2937",
    "surface_alt": "#273445",
    "border": "#4b5563",
    "text": "#f3f4f6",
    "muted": "#cbd5e1",
    "accent": "#60a5fa",
    "accent_text": "#08111f",
    "button": "#374151",
    "button_active": "#4b5563",
    "entry": "#111827",
    "entry_text": "#f9fafb",
    "select": "#1d4ed8",
    "select_text": "#ffffff",
    "drop": "#182233",
}


SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"


def load_settings() -> dict[str, str]:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    theme = data.get("theme", "system")
    if theme not in ("system", "light", "dark"):
        theme = "system"
    return {"theme": theme}


def save_settings(settings: dict[str, str]) -> None:
    with SETTINGS_FILE.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def system_prefers_dark_theme() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _value_type = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except OSError:
        return False


def set_windows_dark_title_bar(window, enabled: bool) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if enabled else 0)
        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            if result == 0:
                break
    except Exception:
        return


class SleepTimerApp:
    def __init__(self, root):
        self.root = root
        self.version = "1.1.1"
        self.root.title(f"Sleep Timer v{self.version}")
        self.root.geometry("300x300")
        self.abort_flag = False

        self.label = ttk.Label(root, text="Select sleep delay:")
        self.label.pack(pady=10)

        self.options = [f"{x} min" for x in [15, 30, 45, 60, 75, 90, 105, 120]]
        self.selected = tk.StringVar(value=self.options[0])
        self.dropdown = tk.OptionMenu(root, self.selected, *self.options)
        self.dropdown.pack()

        self.custom_label = ttk.Label(root, text="Or enter custom time (minutes):")
        self.custom_label.pack(pady=5)
        self.custom_entry = ttk.Entry(root)
        self.custom_entry.pack()

        self.start_button = ttk.Button(
            root, text="Start Countdown", command=self.start_countdown
        )
        self.start_button.pack(pady=10)

        self.abort_button = ttk.Button(
            root, text="Abort", command=self.abort_countdown, state="disabled"
        )
        self.abort_button.pack()

        self.status = ttk.Label(root, text="")
        self.status.pack(pady=5)

        self.settings = load_settings()
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "system"))
        self.system_radio = tk.Radiobutton(root, text="System default", variable=self.theme_var, value="system", command=self._handle_theme_changed)
        self.system_radio.pack()
        self.light_radio = tk.Radiobutton(root, text="Light", variable=self.theme_var, value="light", command=self._handle_theme_changed)
        self.light_radio.pack()
        self.dark_radio = tk.Radiobutton(root, text="Dark", variable=self.theme_var, value="dark", command=self._handle_theme_changed)
        self.dark_radio.pack()

        self.theme = DARK_THEME
        self.style = ttk.Style(self.root)
        self._handle_theme_changed()

    def start_countdown(self):
        try:
            minutes = (
                float(self.custom_entry.get())
                if self.custom_entry.get()
                else int(self.selected.get().split()[0])
            )
            if minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a positive number.")
            return

        self.abort_flag = False
        self.abort_button.config(state="normal")
        self.start_button.config(state="disabled")
        self.status.config(text=f"Countdown started: {minutes:.1f} min")

        threading.Thread(
            target=self.run_countdown, args=(minutes,), daemon=True
        ).start()

    def abort_countdown(self):
        self.abort_flag = True
        self.status.config(text="❌ Countdown aborted.")
        self.abort_button.config(state="disabled")
        self.start_button.config(state="normal")

    def run_countdown(self, minutes):
        total_seconds = int(minutes * 60)

        for remaining in range(total_seconds, 0, -1):
            if self.abort_flag:
                return
            mins, secs = divmod(remaining, 60)
            self.status.config(text=f"🕒 Time left: {mins:02d}:{secs:02d}")
            time.sleep(1)

        self.status.config(text="💤 Sleeping now...")
        self.sleep_start_time = datetime.datetime.now()
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])

        # After sleep returns, report the duration immediately
        self.report_sleep_duration()

    def report_sleep_duration(self):
        wake_time = datetime.datetime.now()
        slept_for = wake_time - self.sleep_start_time
        minutes_slept = slept_for.total_seconds() / 60

        # Use root.after to update GUI from main thread
        self.root.after(
            0,
            lambda: [
                self.status.config(
                    text=f"🌅 Welcome back! Slept for ~{minutes_slept:.1f} min."
                ),
                self.abort_button.config(state="disabled"),
                self.start_button.config(state="normal"),
            ],
        )

    def _effective_theme_name(self) -> str:
        selected_theme = self.theme_var.get()
        if selected_theme == "dark":
            return "dark"
        elif selected_theme == "light":
            return "light"
        else:  # system
            return "dark" if system_prefers_dark_theme() else "light"

    def _handle_theme_changed(self) -> None:
        selected_theme = self.theme_var.get()
        if selected_theme not in ("system", "light", "dark"):
            selected_theme = "system"
            self.theme_var.set(selected_theme)
        self.settings["theme"] = selected_theme
        save_settings(self.settings)
        self.apply_theme()

    def apply_theme(self):
        self.theme = DARK_THEME if self._effective_theme_name() == "dark" else LIGHT_THEME
        self._configure_ttk_theme()
        colors = self.theme
        self._style_widget_tree(self.root)
        set_windows_dark_title_bar(self.root, self._effective_theme_name() == "dark")
        self.root.option_add("*selectBackground", colors["select"])
        self.root.option_add("*selectForeground", colors["select_text"])
        self.dropdown.configure(bg=colors["entry"], fg=colors["entry_text"], activebackground=colors["select"], activeforeground=colors["select_text"])
        menu = self.dropdown['menu']
        menu.configure(bg=colors["entry"], fg=colors["entry_text"], selectcolor=colors["select"])
        self.root.title(f"Sleep Timer v{self.version} - {self.theme_var.get().capitalize()}")

    def _configure_ttk_theme(self):
        try:
            self.style = ttk.Style(self.root)
            self.style.theme_use("clam")
        except Exception:
            pass
        colors = self.theme
        self.style.configure(
            ".",
            background=colors["window"],
            foreground=colors["text"],
            fieldbackground=colors["entry"],
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"],
            troughcolor=colors["surface_alt"],
        )
        self.style.configure(
            "TLabel",
            background=colors["window"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TButton",
            background=colors["button"],
            foreground=colors["text"],
        )
        self.style.map(
            "TButton",
            background=[("active", colors["button_active"]), ("pressed", colors["button_active"])],
            foreground=[("active", colors["text"]), ("pressed", colors["text"])],
        )

        self.style.configure(
            "TEntry",
            fieldbackground=colors["entry"],
            background=colors["entry"],
            foreground=colors["entry_text"],
        )

    def _style_widget_tree(self, widget):
        colors = self.theme
        widget_class = widget.winfo_class()
        try:
            if widget_class in {"Tk", "Toplevel", "Frame", "Labelframe"}:
                widget.configure(background=colors["window"])
            elif isinstance(widget, tk.Canvas):
                widget.configure(background=colors["window"])
            elif isinstance(widget, tk.Label):
                background = colors["drop"] if widget is getattr(self, "drop_area", None) else colors["window"]
                widget.configure(background=background, foreground=colors["text"])
            elif isinstance(widget, tk.Button):
                widget.configure(
                    background=colors["button"],
                    foreground=colors["text"],
                    activebackground=colors["button_active"],
                    activeforeground=colors["text"],
                    highlightbackground=colors["window"],
                    highlightcolor=colors["accent"],
                    relief="raised",
                )
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    background=colors["entry"],
                    foreground=colors["entry_text"],
                    insertbackground=colors["entry_text"],
                    highlightbackground=colors["border"],
                    highlightcolor=colors["accent"],
                )
            elif isinstance(widget, tk.Listbox):
                widget.configure(
                    background=colors["entry"],
                    foreground=colors["entry_text"],
                    selectbackground=colors["select"],
                    selectforeground=colors["select_text"],
                    highlightbackground=colors["border"],
                    highlightcolor=colors["accent"],
                )
            elif isinstance(widget, tk.Radiobutton):
                widget.configure(
                    background=colors["window"],
                    foreground=colors["text"],
                    activebackground=colors["window"],
                    activeforeground=colors["text"],
                    selectcolor=colors["surface_alt"],
                    highlightbackground=colors["window"],
                )
            elif isinstance(widget, tk.Scrollbar):
                widget.configure(
                    background=colors["button"],
                    activebackground=colors["button_active"],
                    troughcolor=colors["surface_alt"],
                    highlightbackground=colors["window"],
                )
        except Exception:
            pass

        for child in widget.winfo_children():
            self._style_widget_tree(child)


if __name__ == "__main__":
    root = tk.Tk()
    app = SleepTimerApp(root)
    root.mainloop()
