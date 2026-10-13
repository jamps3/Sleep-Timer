# Clean Windows App Previews

Install Pillow with `py -m pip install Pillow`, then run:

```powershell
py capture_window.py --list
py capture_window.py --title "Sleep Timer" --background black --output timer-black.png
py capture_window.py --title "Sleep Timer" --background transparent --output timer-transparent.png
```

Running without a title or handle offers a numbered window selector. For duplicate
titles use `--hwnd 0x12345` with a real handle from `--list`. Padding defaults to
24 pixels; use `--padding 0` for the exact client area. Output is always PNG.

The capture intentionally excludes the Windows title bar, frame, rounded corners,
and desktop-blended shadow. App content stays opaque. Transparent mode makes only
the surrounding padding transparent; it does not remove black pixels in the app.
No desktop color changes or screenshot-mode modifications are required.

Restore minimized windows before capture. PrintWindow works well for Tkinter and
many conventional Windows apps, but some GPU-rendered or protected apps may return
blank or incomplete content. Always inspect the output; this is not a universal
capture backend. The tool does not silently fall back to desktop capture.

## Safe Sleep Timer Previews

```powershell
py preview_timer.py --output-dir previews
py -m unittest -v test_capture_window.py
```

The preview runner disables the Start command, Enter binding, and sleep worker.
It exports light and dark client-area previews with both padding options, then
closes the preview window. It does not save theme preferences or suspend the PC.
