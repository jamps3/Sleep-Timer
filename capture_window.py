"""Windows client-area PNG capture. Requires Pillow; never changes the desktop."""
import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path
import sys

from PIL import Image


def padded_image(image, padding=24, background="black"):
    if padding < 0:
        raise ValueError("Padding must be nonnegative")
    color = (0, 0, 0, 0) if background == "transparent" else (0, 0, 0, 255)
    canvas = Image.new("RGBA", (image.width + padding * 2, image.height + padding * 2), color)
    canvas.paste(image.convert("RGBA"), (padding, padding))
    return canvas


def windows_api():
    if sys.platform != "win32":
        raise RuntimeError("Window capture requires Windows")
    user = ctypes.WinDLL("user32", use_last_error=True)
    gdi = ctypes.WinDLL("gdi32", use_last_error=True)
    declarations = [
        (user.GetDC, [wintypes.HWND], wintypes.HDC),
        (user.ReleaseDC, [wintypes.HWND, wintypes.HDC], ctypes.c_int),
        (user.GetClientRect, [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL),
        (user.PrintWindow, [wintypes.HWND, wintypes.HDC, wintypes.UINT], wintypes.BOOL),
        (user.IsWindowVisible, [wintypes.HWND], wintypes.BOOL),
        (user.IsIconic, [wintypes.HWND], wintypes.BOOL),
        (user.GetWindowTextLengthW, [wintypes.HWND], ctypes.c_int),
        (user.GetWindowTextW, [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int),
        (gdi.CreateCompatibleDC, [wintypes.HDC], wintypes.HDC),
        (gdi.CreateCompatibleBitmap, [wintypes.HDC, ctypes.c_int, ctypes.c_int], wintypes.HBITMAP),
        (gdi.SelectObject, [wintypes.HDC, wintypes.HANDLE], wintypes.HANDLE),
        (gdi.DeleteObject, [wintypes.HANDLE], wintypes.BOOL),
        (gdi.DeleteDC, [wintypes.HDC], wintypes.BOOL),
        (gdi.GetDIBits, [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
                        ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT], ctypes.c_int),
    ]
    for function, arguments, result in declarations:
        function.argtypes = arguments
        function.restype = result
    try:
        user.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError:
        user.SetProcessDPIAware()
    return user, gdi


def list_windows():
    user, _ = windows_api()
    result = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def collect(hwnd, _):
        length = user.GetWindowTextLengthW(hwnd)
        if length and user.IsWindowVisible(hwnd):
            title = ctypes.create_unicode_buffer(length + 1)
            user.GetWindowTextW(hwnd, title, len(title))
            result.append((hwnd, title.value))
        return True

    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user.EnumWindows.restype = wintypes.BOOL
    if not user.EnumWindows(collect, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def capture_client(hwnd):
    user, gdi = windows_api()
    if user.IsIconic(hwnd):
        raise RuntimeError("Restore the window before capturing it")
    rect = wintypes.RECT()
    if not user.GetClientRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    width, height = rect.right, rect.bottom
    if width <= 0 or height <= 0:
        raise RuntimeError("The window has no drawable client area")
    dc = user.GetDC(hwnd)
    memory = gdi.CreateCompatibleDC(dc)
    bitmap = gdi.CreateCompatibleBitmap(dc, width, height)
    previous = None
    try:
        if not dc or not memory or not bitmap:
            raise RuntimeError("Could not allocate a window capture buffer")
        previous = gdi.SelectObject(memory, bitmap)
        # PW_CLIENTONLY excludes the OS frame and its desktop-blended shadow.
        if not user.PrintWindow(hwnd, memory, 1):
            raise RuntimeError("This app does not support PrintWindow capture")
        gdi.SelectObject(memory, previous)
        previous = None

        class BitmapHeader(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("width", wintypes.LONG),
                        ("height", wintypes.LONG), ("planes", wintypes.WORD),
                        ("bits", wintypes.WORD), ("compression", wintypes.DWORD),
                        ("image_size", wintypes.DWORD), ("x", wintypes.LONG),
                        ("y", wintypes.LONG), ("used", wintypes.DWORD),
                        ("important", wintypes.DWORD)]

        header = BitmapHeader()
        header.size = ctypes.sizeof(header)
        header.width, header.height = width, -height
        header.planes, header.bits = 1, 32
        pixels = ctypes.create_string_buffer(width * height * 4)
        if gdi.GetDIBits(memory, bitmap, 0, height, pixels, ctypes.byref(header), 0) != height:
            raise RuntimeError("Could not read the complete window image")
        # GDI alpha is undefined: the app content is deliberately fully opaque.
        return Image.frombytes("RGB", (width, height), pixels.raw, "raw", "BGRX")
    finally:
        if previous:
            gdi.SelectObject(memory, previous)
        if bitmap:
            gdi.DeleteObject(bitmap)
        if memory:
            gdi.DeleteDC(memory)
        if dc:
            user.ReleaseDC(hwnd, dc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List visible windows")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--title", help="Exact window title")
    selection.add_argument("--hwnd", type=lambda value: int(value, 0), help="Window handle from --list")
    parser.add_argument("--output", type=Path, default=Path("window-preview.png"))
    parser.add_argument("--background", choices=("black", "transparent"), default="black")
    parser.add_argument("--padding", type=int, default=24)
    args = parser.parse_args()
    try:
        windows = list_windows()
        if args.list:
            for hwnd, title in windows:
                print(f"{hwnd:#x}  {title}")
            return
        if args.padding < 0:
            parser.error("--padding must be nonnegative")
        if args.hwnd is not None:
            matches = [(handle, title) for handle, title in windows if handle == args.hwnd]
        elif args.title:
            matches = [(handle, title) for handle, title in windows if title == args.title]
        else:
            for index, (_, title) in enumerate(windows, 1):
                print(f"{index}. {title}")
            choice = int(input("Window number: "))
            if not 1 <= choice <= len(windows):
                raise ValueError("Choose a listed window number")
            matches = [windows[choice - 1]]
        if len(matches) != 1:
            raise RuntimeError("Select exactly one visible window; use --list and --hwnd for duplicate titles")
        image = capture_client(matches[0][0])
        padded_image(image, args.padding, args.background).save(args.output, format="PNG")
        print(f"Saved {args.output.resolve()} ({image.width} x {image.height} client area)")
    except (OSError, RuntimeError, ValueError, EOFError) as error:
        parser.exit(1, f"Capture failed: {error}\n")


if __name__ == "__main__":
    main()
