"""
Setup script to build InputSourceToggle as a standalone macOS app
Run: python3 setup_app.py py2app
"""

from setuptools import setup

APP = ['input_source_toggle.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'AppIcon.icns',
    'plist': {
        'CFBundleName': 'InputSourceToggle',
        'CFBundleDisplayName': 'Input Source Toggle',
        'CFBundleIdentifier': 'com.ron.inputsourcetoggle',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.15',
        'LSUIElement': True,  # Hide from dock
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright 2024',
    },
    'packages': ['Foundation', 'AppKit', 'Quartz'],
    'includes': ['ctypes', 'ctypes.util', 'signal'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
