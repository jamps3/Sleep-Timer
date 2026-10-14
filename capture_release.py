"""Capture the actual packaged executable in its sleep-disabled preview mode."""
import argparse
from pathlib import Path
import subprocess
import time
from capture_window import capture_client, list_windows, padded_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("previews"))
    parser.add_argument("--running", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        version = (Path(__file__).resolve().parent / 'VERSION').read_text().strip()
        command = [str(args.executable.resolve()), "--preview", theme, "--auto-close-ms", "8000"]
        if args.running:
            command.append("--preview-running")
        process = subprocess.Popen(command)
        try:
            deadline = time.monotonic() + 30
            matches = []
            while time.monotonic() < deadline and process.poll() is None:
                matches = [(hwnd, title) for hwnd, title in list_windows()
                           if title == f"Sleep Timer {version} Preview - {theme}"]
                if len(matches) == 1:
                    break
                time.sleep(0.1)
            if len(matches) != 1:
                raise RuntimeError("Executable preview did not open uniquely")
            time.sleep(0.6)
            image = capture_client(matches[0][0])
            for background in ("black", "transparent"):
                state = "-running" if args.running else ""
                output = args.output_dir / f"sleep-timer-{theme}{state}-{background}.png"
                padded_image(image, 24, background).save(output)
                print(output.resolve())
            if process.wait(timeout=15) != 0:
                raise RuntimeError("Executable preview failed")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
