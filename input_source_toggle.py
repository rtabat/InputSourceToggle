#!/usr/bin/env python3
"""
Input Source Toggle - A macOS menubar app
Toggle between input sources (keyboard languages) using customizable shortcuts
v1.0 by Ron Dickson
"""

import ctypes
import ctypes.util
import json
import os
from Foundation import NSObject, NSLog, NSTimer, NSUserDefaults
from AppKit import (
    NSApplication, NSApp, NSMenu, NSMenuItem, NSStatusBar, NSImage,
    NSVariableStatusItemLength, NSApplicationActivationPolicyAccessory,
    NSAlert, NSAlertStyleInformational, NSOnState, NSOffState
)
from Quartz import (
    CGEventTapCreate, CGEventTapEnable, CGEventMaskBit,
    kCGSessionEventTap, kCGHeadInsertEventTap, kCGEventTapOptionDefault,
    kCGEventFlagsChanged, CGEventGetFlags, CGEventGetIntegerValueField,
    kCGKeyboardEventKeycode, kCGEventFlagMaskShift, kCGEventFlagMaskControl,
    kCGEventFlagMaskCommand, CFMachPortCreateRunLoopSource, CFRunLoopGetCurrent,
    CFRunLoopAddSource, kCFRunLoopCommonModes
)
import signal

APP_VERSION = "1.0"
APP_AUTHOR = "Ron Dickson"

# Load Carbon framework for TIS functions
carbon = ctypes.CDLL('/System/Library/Frameworks/Carbon.framework/Carbon')
cf = ctypes.CDLL(ctypes.util.find_library('CoreFoundation'))

# Set up return types
carbon.TISCreateInputSourceList.restype = ctypes.c_void_p
carbon.TISCreateInputSourceList.argtypes = [ctypes.c_void_p, ctypes.c_bool]

carbon.TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
carbon.TISCopyCurrentKeyboardInputSource.argtypes = []

carbon.TISGetInputSourceProperty.restype = ctypes.c_void_p
carbon.TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

carbon.TISSelectInputSource.restype = ctypes.c_int32
carbon.TISSelectInputSource.argtypes = [ctypes.c_void_p]

cf.CFArrayGetCount.restype = ctypes.c_long
cf.CFArrayGetCount.argtypes = [ctypes.c_void_p]

cf.CFArrayGetValueAtIndex.restype = ctypes.c_void_p
cf.CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_long]

cf.CFStringGetCString.restype = ctypes.c_bool
cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]

cf.CFBooleanGetValue.restype = ctypes.c_bool
cf.CFBooleanGetValue.argtypes = [ctypes.c_void_p]

cf.CFRelease.restype = None
cf.CFRelease.argtypes = [ctypes.c_void_p]

# TIS Property keys
kTISPropertyInputSourceCategory = ctypes.c_void_p.in_dll(carbon, 'kTISPropertyInputSourceCategory')
kTISPropertyInputSourceIsSelectCapable = ctypes.c_void_p.in_dll(carbon, 'kTISPropertyInputSourceIsSelectCapable')
kTISPropertyInputSourceID = ctypes.c_void_p.in_dll(carbon, 'kTISPropertyInputSourceID')
kTISPropertyLocalizedName = ctypes.c_void_p.in_dll(carbon, 'kTISPropertyLocalizedName')
kTISCategoryKeyboardInputSource = ctypes.c_void_p.in_dll(carbon, 'kTISCategoryKeyboardInputSource')

# Shortcut options
SHORTCUT_CTRL_SHIFT = "ctrl_shift"
SHORTCUT_CMD_SHIFT = "cmd_shift"
SHORTCUT_BOTH = "both"


def cfstring_to_string(cfstr):
    """Convert CFString to Python string"""
    if not cfstr:
        return None
    buf = ctypes.create_string_buffer(256)
    if cf.CFStringGetCString(cfstr, buf, 256, 0x08000100):  # kCFStringEncodingUTF8
        return buf.value.decode('utf-8')
    return None


def cfstring_equals(cfstr1, cfstr2):
    """Compare two CFStrings"""
    s1 = cfstring_to_string(cfstr1)
    s2 = cfstring_to_string(cfstr2)
    return s1 == s2


class InputSourceToggleApp(NSObject):
    statusItem = None
    menu = None
    enabled = True
    enableMenuItem = None
    eventTap = None
    ctrl_pressed = False
    cmd_pressed = False
    left_shift_pressed = False
    shortcut_mode = SHORTCUT_CTRL_SHIFT

    # Menu items for shortcuts
    ctrlShiftMenuItem = None
    cmdShiftMenuItem = None
    bothMenuItem = None

    def applicationDidFinishLaunching_(self, notification):
        # Set as accessory app (no dock icon)
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        # Load saved preferences
        self.loadPreferences()

        # Create status bar item
        self.statusItem = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )

        # Set icon
        self.updateIcon()

        # Create menu
        self.menu = NSMenu.new()
        self.menu.setAutoenablesItems_(False)

        # Enable/Disable item
        self.enableMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Enabled", "toggleEnabled:", ""
        )
        self.enableMenuItem.setState_(NSOnState)
        self.enableMenuItem.setTarget_(self)
        self.menu.addItem_(self.enableMenuItem)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Shortcut submenu
        shortcutMenu = NSMenu.alloc().initWithTitle_("Shortcut")

        self.ctrlShiftMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Ctrl + Left Shift", "setCtrlShift:", ""
        )
        self.ctrlShiftMenuItem.setTarget_(self)
        shortcutMenu.addItem_(self.ctrlShiftMenuItem)

        self.cmdShiftMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Cmd + Left Shift", "setCmdShift:", ""
        )
        self.cmdShiftMenuItem.setTarget_(self)
        shortcutMenu.addItem_(self.cmdShiftMenuItem)

        self.bothMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Both", "setBoth:", ""
        )
        self.bothMenuItem.setTarget_(self)
        shortcutMenu.addItem_(self.bothMenuItem)

        shortcutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Shortcut", None, ""
        )
        shortcutItem.setSubmenu_(shortcutMenu)
        self.menu.addItem_(shortcutItem)

        self.updateShortcutMenuState()

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Info item
        infoItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            self.getShortcutDescription(), None, ""
        )
        infoItem.setEnabled_(False)
        infoItem.setTag_(100)  # Tag to find it later
        self.menu.addItem_(infoItem)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # About item
        aboutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About", "showAbout:", ""
        )
        aboutItem.setTarget_(self)
        self.menu.addItem_(aboutItem)

        # Quit item
        quitItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", "q"
        )
        quitItem.setTarget_(self)
        self.menu.addItem_(quitItem)

        self.statusItem.setMenu_(self.menu)

        # Start keyboard monitoring
        self.startMonitoring()

        NSLog("InputSourceToggle started. Press shortcut to toggle input source.")

    def loadPreferences(self):
        """Load saved preferences"""
        defaults = NSUserDefaults.standardUserDefaults()
        mode = defaults.stringForKey_("shortcut_mode")
        if mode and mode in [SHORTCUT_CTRL_SHIFT, SHORTCUT_CMD_SHIFT, SHORTCUT_BOTH]:
            self.shortcut_mode = mode

    def savePreferences(self):
        """Save preferences"""
        defaults = NSUserDefaults.standardUserDefaults()
        defaults.setObject_forKey_(self.shortcut_mode, "shortcut_mode")
        defaults.synchronize()

    def getShortcutDescription(self):
        """Get human-readable shortcut description"""
        if self.shortcut_mode == SHORTCUT_CTRL_SHIFT:
            return "⌃ Ctrl + Left Shift to toggle"
        elif self.shortcut_mode == SHORTCUT_CMD_SHIFT:
            return "⌘ Cmd + Left Shift to toggle"
        else:
            return "⌃/⌘ + Left Shift to toggle"

    def updateShortcutMenuState(self):
        """Update checkmarks on shortcut menu items"""
        self.ctrlShiftMenuItem.setState_(NSOnState if self.shortcut_mode == SHORTCUT_CTRL_SHIFT else NSOffState)
        self.cmdShiftMenuItem.setState_(NSOnState if self.shortcut_mode == SHORTCUT_CMD_SHIFT else NSOffState)
        self.bothMenuItem.setState_(NSOnState if self.shortcut_mode == SHORTCUT_BOTH else NSOffState)

        # Update info text
        infoItem = self.menu.itemWithTag_(100)
        if infoItem:
            infoItem.setTitle_(self.getShortcutDescription())

    def setCtrlShift_(self, sender):
        self.shortcut_mode = SHORTCUT_CTRL_SHIFT
        self.updateShortcutMenuState()
        self.savePreferences()
        NSLog("Shortcut set to Ctrl + Left Shift")

    def setCmdShift_(self, sender):
        self.shortcut_mode = SHORTCUT_CMD_SHIFT
        self.updateShortcutMenuState()
        self.savePreferences()
        NSLog("Shortcut set to Cmd + Left Shift")

    def setBoth_(self, sender):
        self.shortcut_mode = SHORTCUT_BOTH
        self.updateShortcutMenuState()
        self.savePreferences()
        NSLog("Shortcut set to Both")

    def showAbout_(self, sender):
        """Show about dialog"""
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Input Source Toggle")
        alert.setInformativeText_(
            f"Version {APP_VERSION}\n\n"
            f"by {APP_AUTHOR}\n\n"
            "Quickly switch between English and Hebrew\n"
            "keyboard layouts using a keyboard shortcut."
        )
        alert.setAlertStyle_(NSAlertStyleInformational)
        alert.addButtonWithTitle_("OK")

        # Set icon
        icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "globe", "Globe"
        )
        if icon:
            alert.setIcon_(icon)

        alert.runModal()

    def updateIcon(self):
        if self.statusItem:
            button = self.statusItem.button()
            if button:
                # Use SF Symbol for globe/language icon
                if self.enabled:
                    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                        "globe", "Input Toggle"
                    )
                else:
                    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                        "globe.badge.chevron.backward", "Input Toggle (Disabled)"
                    )
                if image:
                    image.setTemplate_(True)
                    button.setImage_(image)
                else:
                    # Fallback to text if symbol not available
                    button.setTitle_("🌐")

    def toggleEnabled_(self, sender):
        self.enabled = not self.enabled
        self.enableMenuItem.setState_(NSOnState if self.enabled else NSOffState)
        self.updateIcon()
        NSLog(f"InputSourceToggle {'enabled' if self.enabled else 'disabled'}")

    def quitApp_(self, sender):
        NSLog("InputSourceToggle quitting...")
        if self.eventTap:
            CGEventTapEnable(self.eventTap, False)
        NSApp.terminate_(self)

    def startMonitoring(self):
        # Store reference to self for callback
        app = self

        # Create callback for keyboard events
        def callback(proxy, event_type, event, refcon):
            if not app.enabled:
                return event

            flags = CGEventGetFlags(event)
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)

            ctrl_down = bool(flags & kCGEventFlagMaskControl)
            cmd_down = bool(flags & kCGEventFlagMaskCommand)
            shift_down = bool(flags & kCGEventFlagMaskShift)

            # Left Shift keycode is 56
            # Left Control keycode is 59, Right Control is 62
            # Left Command keycode is 55, Right Command is 54
            if keycode in (59, 62):  # Control key
                app.ctrl_pressed = ctrl_down

            if keycode in (55, 54):  # Command key
                app.cmd_pressed = cmd_down

            if keycode == 56:  # Left Shift
                if shift_down:
                    app.left_shift_pressed = True
                else:
                    # Left shift released - check if we should toggle
                    should_toggle = False

                    if app.left_shift_pressed:
                        if app.shortcut_mode == SHORTCUT_CTRL_SHIFT and app.ctrl_pressed:
                            should_toggle = True
                        elif app.shortcut_mode == SHORTCUT_CMD_SHIFT and app.cmd_pressed:
                            should_toggle = True
                        elif app.shortcut_mode == SHORTCUT_BOTH and (app.ctrl_pressed or app.cmd_pressed):
                            should_toggle = True

                    if should_toggle:
                        app.toggleInputSource()

                    app.left_shift_pressed = False

            # Reset if modifiers released
            if not ctrl_down:
                app.ctrl_pressed = False
            if not cmd_down:
                app.cmd_pressed = False

            return event

        # Create event tap
        mask = CGEventMaskBit(kCGEventFlagsChanged)
        self.eventTap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionDefault,
            mask,
            callback,
            None
        )

        if not self.eventTap:
            NSLog("ERROR: Failed to create event tap. Please grant Accessibility permissions.")
            NSLog("Go to System Preferences > Privacy & Security > Accessibility")
            # Show alert
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Accessibility Permission Required")
            alert.setInformativeText_(
                "Please grant Accessibility permission in System Preferences > "
                "Privacy & Security > Accessibility, then restart the app."
            )
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return

        # Add to run loop
        runLoopSource = CFMachPortCreateRunLoopSource(None, self.eventTap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, kCFRunLoopCommonModes)
        CGEventTapEnable(self.eventTap, True)
        NSLog("Keyboard monitoring started")

    def toggleInputSource(self):
        """Toggle to the next input source"""
        try:
            # Get all input sources
            sources = carbon.TISCreateInputSourceList(None, False)
            if not sources:
                return

            count = cf.CFArrayGetCount(sources)

            # Filter to selectable keyboard input sources
            selectable = []
            for i in range(count):
                source = cf.CFArrayGetValueAtIndex(sources, i)

                category = carbon.TISGetInputSourceProperty(
                    source, kTISPropertyInputSourceCategory
                )
                is_selectable = carbon.TISGetInputSourceProperty(
                    source, kTISPropertyInputSourceIsSelectCapable
                )

                # Check if keyboard input source and selectable
                if category and is_selectable:
                    if cfstring_equals(category, kTISCategoryKeyboardInputSource):
                        if cf.CFBooleanGetValue(is_selectable):
                            selectable.append(source)

            if len(selectable) < 2:
                cf.CFRelease(sources)
                return

            # Get current source
            current = carbon.TISCopyCurrentKeyboardInputSource()
            current_id = carbon.TISGetInputSourceProperty(
                current, kTISPropertyInputSourceID
            )
            current_id_str = cfstring_to_string(current_id)

            # Find current index
            current_idx = 0
            for i, source in enumerate(selectable):
                source_id = carbon.TISGetInputSourceProperty(
                    source, kTISPropertyInputSourceID
                )
                if cfstring_to_string(source_id) == current_id_str:
                    current_idx = i
                    break

            # Select next source
            next_idx = (current_idx + 1) % len(selectable)
            next_source = selectable[next_idx]
            carbon.TISSelectInputSource(next_source)

            # Log the change
            next_name = carbon.TISGetInputSourceProperty(
                next_source, kTISPropertyLocalizedName
            )
            name_str = cfstring_to_string(next_name)
            NSLog(f"Switched to: {name_str}")

            # Brief visual feedback
            self.showFeedback()

            # Clean up
            cf.CFRelease(sources)
            cf.CFRelease(current)

        except Exception as e:
            NSLog(f"Error toggling input source: {e}")

    def showFeedback(self):
        """Show brief visual feedback on icon"""
        if self.statusItem:
            button = self.statusItem.button()
            if button:
                image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                    "globe.americas.fill", "Input Switched"
                )
                if image:
                    image.setTemplate_(True)
                    button.setImage_(image)

                # Reset after delay
                NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    0.3, self, "resetIcon:", None, False
                )

    def resetIcon_(self, timer):
        self.updateIcon()


def main():
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        NSLog("Received interrupt signal, quitting...")
        NSApp.terminate_(None)

    signal.signal(signal.SIGINT, signal_handler)

    # Create and run app
    app = NSApplication.sharedApplication()
    delegate = InputSourceToggleApp.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
