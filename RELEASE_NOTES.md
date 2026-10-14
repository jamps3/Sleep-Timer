# Sleep Timer 1.1.3

Released: 2026-10-15. Windows x64, unsigned standalone executable.

- Window title displays 1.1.3, read from the same VERSION file used by the build.
- Cancel is red while a countdown runs, including after theme changes.
- Theme-aware hover feedback on preset, Start and Cancel buttons; disabled
  buttons do not change appearance on hover.
- Added 1, 2, 3 and 5 minute presets; all eight earlier presets remain.
- VERSION is bundled in the executable so its title cannot use an old hardcoded value.

Verification: nine safe source/GUI tests pass. Packaged idle and running preview
modes tested in light/dark themes without invoking Windows sleep. Real system
suspend/wake remains untested. Previous release executables are preserved.

SHA256 (`dist/SleepTimer_1.1.3.exe`):

```text
d7b6f8076520efefbd044690e14b5f8ca2d5dd674d63574c54d1d9aa0832ecf3
```

## Sleep Timer 1.1.2

Released: 2026-10-13. Windows x64, unsigned standalone executable.

- Large, high-contrast controls with all eight minute presets visible.
- Custom whole-minute input limited to seven digits.
- Live countdown, scheduled sleep time and progress.
- Persistent light, dark and system themes; settings beside the executable.
- Tkinter updates remain on the UI thread, with a monotonic countdown.
- Adaptive height prevents clipped action controls at the tested display scaling.
- Build spec supports this installation's embedded Tcl/Tk 9 libraries.
- Sleep-disabled preview mode for reproducible executable screenshots.

Verification: six source tests pass, and the packaged executable opens, renders
both themes, exports previews and exits cleanly. Real Windows sleep/wake behavior
is not tested. No shutdown or hibernation feature is claimed.

SHA256 (`dist/SleepTimer_1.1.2.exe`):

```text
80beb8a16c5b3a19d1e4061164ecca1df63235a4a1363416acaa27e413acbcaa
```
