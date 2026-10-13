"""Create safe Sleep Timer previews without ever invoking Windows sleep."""
import argparse
from pathlib import Path
import tkinter as tk

import capture_window
import sleep_timer_gui


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("previews"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    app = sleep_timer_gui.SleepTimerApp(root)
    app._suspend = lambda: app.events.put((False, "Preview mode: sleep disabled"))
    app.start_button.config(command=lambda: None)
    root.unbind("<Return>")

    def capture(theme):
        app.theme_var.set(theme)
        app.apply_theme()
        root.update_idletasks()
        # Resolve the native outer window, not Tk's child drawing handle.
        import ctypes
        from ctypes import wintypes
        user = ctypes.WinDLL("user32")
        user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user.GetAncestor.restype = wintypes.HWND
        hwnd = user.GetAncestor(root.winfo_id(), 2)
        image = capture_window.capture_client(hwnd)
        for background in ("black", "transparent"):
            capture_window.padded_image(image, 24, background).save(
                args.output_dir / f"sleep-timer-{theme}-{background}.png")
        if theme == "light":
            root.after(400, lambda: capture("dark"))
        else:
            app.close()

    root.after(600, lambda: capture("light"))
    root.mainloop()


if __name__ == "__main__":
    main()
