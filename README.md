# InputSourceToggle

A macOS menubar app that toggles between keyboard input sources (languages) using customizable keyboard shortcuts. Built for quickly switching between English and Hebrew layouts.

## Features

- Lives in the menubar (no Dock icon)
- Customizable keyboard shortcuts:
  - Ctrl + Left Shift
  - Cmd + Left Shift
  - Both (either modifier works)
- Visual feedback on toggle
- Preferences persistence
- Auto-start on login via LaunchAgent

## Requirements

- macOS 10.15 (Catalina) or later
- Python 3
- Accessibility permissions (for keyboard event monitoring)

## Dependencies

- [PyObjC](https://pyobjc.readthedocs.io/) (Foundation, AppKit, Quartz)
- [py2app](https://py2app.readthedocs.io/) (for building the standalone .app)
- [Pillow](https://pillow.readthedocs.io/) (for icon generation only)

## Building

Generate the app icon (if needed):

```bash
python3 create_icon.py
```

Build the standalone macOS app:

```bash
python3 setup_app.py py2app
```

The built app will be in `dist/InputSourceToggle.app`.

## Running

For development:

```bash
./run.sh
```

To install as a LaunchAgent (auto-start on login):

```bash
./setup.sh
```

## Author

Ron Dickson
