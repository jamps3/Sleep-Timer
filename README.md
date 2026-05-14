# Sleep Timer

A simple GUI application for Windows that schedules your computer to go to sleep after a specified countdown time.

## Features

- **Preset Timers**: Choose from common sleep delays (15, 30, 45, 60, 75, 90, 105, 120 minutes).
- **Custom Timer**: Enter any custom time in minutes.
- **Countdown Display**: Real-time countdown showing remaining time.
- **Abort Functionality**: Cancel the countdown at any time.
- **Theme Support**: Light, Dark, or System default theme with persistence.
- **Sleep Tracking**: Displays how long you actually slept upon wake-up.

## Requirements

- Python 3.6+
- tkinter (usually included with Python)
- Windows OS (uses Windows-specific sleep command)

## Installation

1. Clone or download the repository.
2. Ensure Python is installed.
3. Run the application: `python sleep_timer_gui.py`

## Usage

1. Select a sleep delay from the dropdown or enter a custom time.
2. Click "Start Countdown" to begin the timer.
3. The app will show the remaining time.
4. Your computer will enter sleep mode when the timer reaches zero.
5. Upon waking, the app displays how long you slept.

To abort the countdown, click the "Abort" button.

## Themes

- **System Default**: Matches your Windows theme preference.
- **Light**: Light color scheme.
- **Dark**: Dark color scheme with dark title bar on Windows.

Theme selection is saved and persists between sessions.

## Notes

- This application uses Windows' built-in sleep functionality.
- Ensure you save any work before starting the timer.
- The app will resume and show sleep duration after wake-up.

## License

[Add your license here, e.g., MIT]</content>
<parameter name="filePath">README.md