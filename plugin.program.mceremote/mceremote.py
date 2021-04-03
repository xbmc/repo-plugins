"""
************************************************************************
MCERemote Addon
Author: John Rennie
v2.0.5 16th March 2014

This addon allows you to configure a Microsoft MCE remote, or any
compatible remote using the eHome driver.

The addon modifies the ReportMappingTable registry entry to configure
the remote to send the standard MCE keyboard shortcuts. See
http://msdn.microsoft.com/en-us/library/bb189249.aspx for details.

The addon can also reset the ReportMappingTable registry entry to the
default for a freshly installed MCE remote.
************************************************************************
"""

import sys
import winreg
import platform
import xbmcvfs
import xbmcplugin
import xbmcgui
import xbmcaddon

# Save the ID of this plugin - cast to integer
_thisPlugin = int(sys.argv[1])

# Name of the plugin
_thisPluginName = "plugin.program.mceremote"

# Addon object for reading settings
_settings = xbmcaddon.Addon(id=_thisPluginName)

# Registry key where the ReportMappingTable is stored
_ReportMappingTable = "SYSTEM\\CurrentControlSet\\Services\\HidIr\\Remotes\\745a17a0-74d3-11d0-b6fe-00a0c90f57da"

# Path to our data directory
_AddonDir = xbmcvfs.validatePath(_settings.getAddonInfo("path") + "/")
_DataDir  = xbmcvfs.validatePath(_AddonDir + "resources/data/")

# Data for the remote control buttons
# The array contains tuples of (button_name, button_number, default_setting, mce_default)
_buttonData = (
  ("button_0",          0x00, "0",            [0x04,0x00,0x27]),
  ("button_1",          0x01, "1",            [0x04,0x00,0x1e]),
  ("button_2",          0x02, "2",            [0x04,0x00,0x1f]),
  ("button_3",          0x03, "3",            [0x04,0x00,0x20]),
  ("button_4",          0x04, "4",            [0x04,0x00,0x21]),
  ("button_5",          0x05, "5",            [0x04,0x00,0x22]),
  ("button_6",          0x06, "6",            [0x04,0x00,0x23]),
  ("button_7",          0x07, "7",            [0x04,0x00,0x24]),
  ("button_8",          0x08, "8",            [0x04,0x00,0x25]),
  ("button_9",          0x09, "9",            [0x04,0x00,0x26]),
  ("button_clear",      0x0a, "escape",       [0x04,0x00,0x29]),
  ("button_enter",      0x0b, "return",       [0x04,0x00,0x28]),
  ("button_power",      0x0c, "",             [0x03,0x82,0x00]),
  ("button_windows",    0x0d, "ctrl-shift-w", []),
  ("button_mute",       0x0e, "f8",           [0x01,0xe2,0x00]),
  ("button_info",       0x0f, "ctrl-d",       [0x01,0x09,0x02]),
  ("button_volup",      0x10, "f10",          [0x01,0xe9,0x00]),
  ("button_voldown",    0x11, "f9",           [0x01,0xea,0x00]),
  ("button_chanup",     0x12, "pageup",       [0x01,0x9c,0x00]),
  ("button_chandown",   0x13, "pagedown",     [0x01,0x9d,0x00]),
  ("button_ff",         0x14, "ctrl-shift-f", [0x01,0xb3,0x00]),
  ("button_rew",        0x15, "ctrl-shift-b", [0x01,0xb4,0x00]),
  ("button_play",       0x16, "ctrl-shift-p", [0x01,0xb0,0x00]),
  ("button_record",     0x17, "ctrl-r",       [0x01,0xb2,0x00]),
  ("button_pause",      0x18, "ctrl-p",       [0x01,0xb1,0x00]),
  ("button_stop",       0x19, "ctrl-shift-s", [0x01,0xb7,0x00]),
  ("button_next",       0x1a, "ctrl-f",       [0x01,0xb5,0x00]),
  ("button_prev",       0x1b, "ctrl-b",       [0x01,0xb6,0x00]),
  ("button_hash",       0x1c, "ctrl-shift-3", [0x04,0x02,0x20]),
  ("button_star",       0x1d, "ctrl-shift-8", [0x04,0x02,0x25]),
  ("button_up",         0x1e, "up",           [0x04,0x00,0x52]),
  ("button_down",       0x1f, "down",         [0x04,0x00,0x51]),
  ("button_left",       0x20, "left",         [0x04,0x00,0x50]),
  ("button_right",      0x21, "right",        [0x04,0x00,0x4f]),
  ("button_ok",         0x22, "return",       [0x04,0x00,0x28]),
  ("button_back",       0x23, "backspace",    [0x01,0x24,0x02]),
  ("button_dvdmenu",    0x24, "ctrl-shift-m", []),
  ("button_livetv",     0x25, "ctrl-shift-t", []),
  ("button_guide",      0x26, "ctrl-g",       [0x01,0x8d,0x00]),
  ("button_asrock",     0x27, "ctrl-alt-t",   []),

  ("button_xbopen",     0x28, "",   []),               # Open/Close on XBox universal remote
  ("button_hpwron",     0x29, "",   [0x03,0x83,0x00]), # Harmony discrete power on
  ("button_hpwroff",    0x2a, "",   [0x03,0x82,0x00]), # Harmony discrete power off

  ("button_unkwn",      0x3b, "",   [0x01,0x04,0x02]), # Unknown button

  ("button_music",      0x47, "ctrl-m",       []),
  ("button_recordedtv", 0x48, "ctrl-o",       []),
  ("button_pictures",   0x49, "ctrl-i",       []),
  ("button_movies",     0x4A, "ctrl-e",       []),

  ("button_mgangle",    0x4b, "",   []),                        # Mediagate DVD Angle
  ("button_mgaudio",    0x4c, "",   []),                        # Mediagate DVD Audio
  ("button_mgsubtitle", 0x4d, "",   []),                        # Mediagate Subtitles
  ("button_hpprint",    0x4e, "ctrl-alt-p", [0x01,0x08,0x02]),  # Print on HP remote
  ("button_xbdisplay",  0x4f, "",   []),                        # Display on XBox universal remote

  ("button_radio",      0x50, "ctrl-a",       []),
  ("button_teletext",   0x5a, "ctrl-t",       []),
  ("button_red",        0x5b, "ctrl-alt-1",   []),
  ("button_green",      0x5c, "ctrl-alt-2",   []),
  ("button_yellow",     0x5d, "ctrl-alt-3",   []),
  ("button_blue",       0x5e, "ctrl-alt-4",   []),

  ("button_xblargex",   0x64, "",   []),                # Large X on XBox universal remote
  ("button_xbgreena",   0x66, "",   []),                # Green A on XBox universal remote
  ("button_xbbluex",    0x68, "",   []),                # Blue  X on XBox universal remote
  ("button_xbchanup",   0x6c, "",   []),                # Chan up on XBox universal remote
  ("button_xbchandn",   0x6d, "",   []),                # Chan dn on XBox universal remote
  ("button_playpause",  0x6e, "",   [0x01,0xcd,0x00]), # Play/pause on HP remote
)

# Key to eHome character code mapping table
_KeyToeHomeCode = (
  ("a",0x04),
  ("b",0x05),
  ("c",0x06),
  ("d",0x07),
  ("e",0x08),
  ("f",0x09),
  ("g",0x0A),
  ("h",0x0B),
  ("i",0x0C),
  ("j",0x0D),
  ("k",0x0E),
  ("l",0x0F),
  ("m",0x10),
  ("n",0x11),
  ("o",0x12),
  ("p",0x13),
  ("q",0x14),
  ("r",0x15),
  ("s",0x16),
  ("t",0x17),
  ("u",0x18),
  ("v",0x19),
  ("w",0x1A),
  ("x",0x1B),
  ("y",0x1C),
  ("z",0x1D),
  ("1",0x1E),
  ("!",0x1E),
  ("2",0x1F),
  ("@",0x1F),
  ("3",0x20),
  ("#",0x20),
  ("4",0x21),
  ("$",0x21),
  ("5",0x22),
  ("%",0x22),
  ("6",0x23),
  ("^",0x23),
  ("7",0x24),
  ("&",0x24),
  ("8",0x25),
  ("*",0x25),
  ("9",0x26),
  ("(",0x26),
  ("0",0x27),
  (")",0x27),
  ("return",0x28),
  ("escape",0x29),
  ("esc",0x29),
  ("backspace",0x2A),
  ("tab",0x2B),
  ("space",0x2C),
  ("-",0x2D),
  ("_",0x2D),
  ("=",0x2E),
  ("+",0x2E),
  ("[",0x2F),
  ("{",0x2F),
  ("]",0x30),
  ("}",0x30),
  ("\\",0x31),
  ("|",0x31),
  (";",0x33),
  (":",0x33),
  ("'",0x34),
  ("\"",0x34),
  ("`",0x35),
  ("~",0x35),
  (",",0x36),
  ("<",0x36),
  (".",0x37),
  (">",0x37),
  ("/",0x38),
  ("?",0x38),
  ("f1",0x3A),
  ("f2",0x3B),
  ("f3",0x3C),
  ("f4",0x3D),
  ("f5",0x3E),
  ("f6",0x3F),
  ("f7",0x40),
  ("f8",0x41),
  ("f9",0x42),
  ("f10",0x43),
  ("f11",0x44),
  ("f12",0x45),
  ("insert", 0x49),
  ("ins", 0x49),
  ("home", 0x4A),
  ("pageup", 0x4B),
  ("pgup", 0x4B),
  ("delete", 0x4C),
  ("del", 0x4C),
  ("end", 0x4D),
  ("pagedown", 0x4E),
  ("pgdown", 0x4E),
  ("pgdn", 0x4E),
  ("right", 0x4F),
  ("left", 0x50),
  ("down", 0x51),
  ("up", 0x52)
)


# **********************************************************************
# local_string
# ------------
# Retrieve a string from strings.po
# **********************************************************************
def local_string(string_id):
	return _settings.getLocalizedString(string_id)


# **********************************************************************
# CheckRegKey
# -----------
# Check for the presence of the ReportMappingTable registry value.
# Return true if the registry value is found or false if the registry
# value is not present.
# **********************************************************************
def CheckRegKey():

    try:
        hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _ReportMappingTable)
        rmp = winreg.QueryValueEx(hkey, "ReportMappingTable")
        foundkey = True
        winreg.CloseKey(hkey)

    except:
        foundkey = False

    return foundkey


# **********************************************************************
# ConvertKeyText
# --------------
# Convert the text representation of a key e.g. ctr;-shift-P into the
# three character representation required by the eHome driver.
# **********************************************************************
def ConvertKeyText(KeyText, Default):

    keymod = 0
    keycode = 0
    ehomecode = []

    keytext = KeyText.replace(" ", "").lower()
    if keytext == "":
        return ehomecode

# If the key text is "mce" return the default

    if keytext == "mce":
        return Default

# Check for key modifiers

    i = keytext.find("ctrl-")
    if i != -1:
        keymod = keymod | 1
        keytext = keytext[:i] + keytext[i+5:]

    i = keytext.find("control-")
    if i != -1:
        keymod = keymod | 1
        keytext = keytext[:i] + keytext[i+8:]

    i = keytext.find("shift-")
    if i != -1:
        keymod = keymod | 2
        keytext = keytext[:i] + keytext[i+6:]

    i = keytext.find("alt-")
    if i != -1:
        keymod = keymod | 4
        keytext = keytext[:i] + keytext[i+4:]

    i = keytext.find("win-")
    if i != -1:
        keymod = keymod | 8
        keytext = keytext[:i] + keytext[i+4:]

    i = keytext.find("super-")
    if i != -1:
        keymod = keymod | 8
        keytext = keytext[:i] + keytext[i+6:]

# There should be just the character remaining

    for ehomekey in _KeyToeHomeCode:
        if ehomekey[0] == keytext:
            keycode = ehomekey[1]
            break

# Return the converted key text

    ehomecode = [0x04, keymod, keycode]

    return ehomecode


# **********************************************************************
# ApplyCurrentSettings
# --------------------
# Read the addon settings and use them to configure the remote
# **********************************************************************
def ApplyCurrentSettings(Prompt):

# Require confirmation from the user

    dialog = xbmcgui.Dialog()

    if Prompt:
        if not dialog.yesno(local_string(30300), local_string(30303)):
            return

# Build the settings string from the _buttonData

    reportmappingtable = []

    for button in _buttonData:
        # keytext is the text entered by the user
        keytext = _settings.getSetting(button[0])

        # if the user has entered "mce" but the button table contains no
        # default, set the keytext to "" so it will be ignored.
        if keytext == "mce" and len(button[3]) == 0:
            keytext = ""

        if keytext != "":
            thisbutton = ConvertKeyText(keytext, button[3])
            if len(thisbutton) != 3:
                dialog.ok(local_string(30300), local_string(30304).format(button[0], keytext))
                return

            reportmappingtable.append(button[1])
            reportmappingtable.append(0)
            reportmappingtable.append(0)
            reportmappingtable.append(0)
            for i in thisbutton:
                reportmappingtable.append(i)

# Open the registry key

    try:
        hkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, _ReportMappingTable, 0, winreg.KEY_SET_VALUE)
    except WindowsError as e:
        dialog.ok(local_string(30300), local_string(30305).format(e.args[1]))
        return
    except:
        dialog.ok(local_string(30300), local_string(30306))
        return

# Write the ReportMappingTable data

    try:
        winreg.SetValueEx(hkey, "ReportMappingTable", 0, winreg.REG_BINARY, bytes(reportmappingtable))
    except Exception as e:
        dialog.ok(local_string(30300), local_string(30307).format(e.args[0]))
    except:
        dialog.ok(local_string(30300), local_string(30308))

# Finished!

    winreg.CloseKey(hkey)
    dialog.ok(local_string(30300), local_string(30309))


# **********************************************************************
# ApplyDefaultSettings
# --------------------
# Restore the default Windows ReportMappingTable.
# **********************************************************************
def ApplyDefaultSettings(Prompt):

# Require confirmation from the user

    dialog = xbmcgui.Dialog()

    if Prompt:
        if not dialog.yesno(local_string(30300), local_string(30310)):
            return

# Open the registry key

    try:
        hkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, _ReportMappingTable, 0, winreg.KEY_SET_VALUE)
    except WindowsError as e:
        dialog.ok(local_string(30300), local_string(30305).format(e.args[1]))
        return
    except:
        dialog.ok(local_string(30300), local_string(30306))
        return

# Build the settings list from the _buttonData

    reportmappingtable = []

    for button in _buttonData:
        if len(button[3]) == 3:
            reportmappingtable.append(button[1])
            reportmappingtable.append(0)
            reportmappingtable.append(0)
            reportmappingtable.append(0)
            for i in button[3]:
                reportmappingtable.append(i)

# Write the ReportMappingTable data

    try:
        winreg.SetValueEx(hkey, "ReportMappingTable", 0, winreg.REG_BINARY, bytes(reportmappingtable))
    except Exception as e:
        dialog.ok(local_string(30300), local_string(30307).format(e.args[0]))
    except:
        dialog.ok(local_string(30300), local_string(30308))

# Finished!

    winreg.CloseKey(hkey)
    dialog.ok(local_string(30300), local_string(30309))


# **********************************************************************
# ConfigureButtonSettings
# -----------------------
# Open the dialog to configure the settings
# **********************************************************************
def ConfigureButtonSettings():

# Open the settings dialog

    _settings.openSettings()

# Ask the user if they want to apply these settings

    if xbmcgui.Dialog().yesno(local_string(30300), local_string(30311)):
        ApplyCurrentSettings(False)


# **********************************************************************
# RestoreDefaultButtonSettings
# ----------------------------
# Restore the default settings
# **********************************************************************
def RestoreDefaultButtonSettings():

# Require confirmation from the user

    dialog = xbmcgui.Dialog()
    if not dialog.yesno(local_string(30300), local_string(30312)):
        return

# Restore the default settings from the info in _buttonData

    for nextbutton in _buttonData:
        _settings.setSetting(nextbutton[0], nextbutton[2])

# Ask the user if they want to apply these settings

    if xbmcgui.Dialog().yesno(local_string(30300), local_string(30311)):
        ApplyCurrentSettings(False)


# **********************************************************************
# EditKeyboardDotXML
# --------------------
# Edit the keyboard.xml in the user's userdata\keymaps folder.
# **********************************************************************
def EditKeyboardDotXML():

    import os
    import shutil
    import subprocess

    dialog = xbmcgui.Dialog()

# Check whether keyboard.xml exists

    dstpath = xbmcvfs.translatePath("special://home/userdata/keymaps/keyboard.xml")
    if not os.path.isfile(dstpath):
        if dialog.yesno(local_string(30300), local_string(30313)):
            CreateKeyboardDotXML()
        else:
            return

# Select the keymap editor: if KeyMapEdit.exe exists use it, otherwise
# use Notepad.

    srcpath = shutil.which("keymapedit.exe")
    if srcpath == None:
        srcpath = "notepad.exe"

# Edit the keyboard.xml in Notepad

    child = subprocess.Popen(srcpath + ' "' + dstpath + '"')
    rc = child.wait()
    ourpath = xbmcvfs.translatePath("special://xbmcbin/")
    child = subprocess.Popen(ourpath + "kodi.exe")

# Now parse the file to check for any obvious errors

    import xml.dom.minidom

    try:
        doc = xml.dom.minidom.parse(dstpath)

    except xml.parsers.expat.ExpatError as e:
        dialog.ok(local_string(30300), local_string(30314).format(e.args[0]))

    except:
        dialog.ok(local_string(30300), local_string(30315))


# **********************************************************************
# CreateKeyboardDotXML
# --------------------
# Copy the template keyboard.xml from resources\data to the user's
# userdata\keymaps folder.
# **********************************************************************
def CreateKeyboardDotXML():
    """
    Create a template keyboard.xml
    @return void
    """

    import os
    import shutil
    import subprocess

    dialog = xbmcgui.Dialog()

# Find the template file: try the profile first

    srcpath = _DataDir + "keyboard.xml"
    if not os.path.isfile(srcpath):
        srcpath = xbmcvfs.translatePath("special://xbmc/addons/" + _thisPluginName + "/resources/data/keyboard.xml")

    if not os.path.isfile(srcpath):
        dialog.ok(local_string(30300), local_string(30316))
        return

# Check whether a keyboard.xml already exists

    dstpath = xbmcvfs.translatePath("special://home/userdata/keymaps/keyboard.xml")
    if os.path.isfile(dstpath):
        if not dialog.yesno(local_string(30300), local_string(30317).format(dstpath)):
            return

    elif not dialog.yesno(local_string(30300), local_string(30318).format(dstpath)):
        return

# Copy the template keyboard.xml

    try:
        shutil.copyfile(srcpath, dstpath)
    except:
        dialog.ok(local_string(30300), local_string(30319))


# **********************************************************************
# ReadInstructions
# ----------------
# Display the instructions in Notepad
# **********************************************************************
def ReadInstructions():

    import os
    import subprocess

# Find the Readme file: try the profile first

    ourpath = _AddonDir + "ReadMeFirst.txt"
    if not os.path.isfile(ourpath):
        ourpath = xbmcvfs.translatePath("special://xbmc/addons/" + _thisPluginName + "/ReadMeFirst.txt")

    if not os.path.isfile(ourpath):
        dialog = xbmcgui.Dialog()
        dialog.ok(local_string(30300), local_string(30320))
        return

# Open the readme file in Notepad

    child = subprocess.Popen('notepad.exe "' + ourpath + '"')
    rc = child.wait()

# Run XBMC: this will simply set the focus back to the current instance

    ourpath = xbmcvfs.translatePath("special://xbmcbin/")
    child = subprocess.Popen(ourpath + "kodi.exe")


# **********************************************************************
# ListOptions
# -----------
# List the MCERemote options
# **********************************************************************
def ListOptions():

    #Add the options
    listItem = xbmcgui.ListItem(local_string(30321))
    xbmcplugin.addDirectoryItem(_thisPlugin, "plugin://" + _thisPluginName + "?instructions", listItem)

    listItem = xbmcgui.ListItem(local_string(30322))
    xbmcplugin.addDirectoryItem(_thisPlugin,"plugin://" + _thisPluginName + "?applycurrentsettings", listItem)

    listItem = xbmcgui.ListItem(local_string(30323))
    xbmcplugin.addDirectoryItem(_thisPlugin, "plugin://" + _thisPluginName + "?applydefaultsettings", listItem)

    listItem = xbmcgui.ListItem(local_string(30324))
    xbmcplugin.addDirectoryItem(_thisPlugin, "plugin://" + _thisPluginName + "?configurebuttons", listItem)

    listItem = xbmcgui.ListItem(local_string(30325))
    xbmcplugin.addDirectoryItem(_thisPlugin, "plugin://" + _thisPluginName + "?defaultbuttons", listItem)

    listItem = xbmcgui.ListItem(local_string(30326))
    xbmcplugin.addDirectoryItem(_thisPlugin, "plugin://" + _thisPluginName + "?editkeyboarddotxml", listItem)

    xbmcplugin.endOfDirectory(_thisPlugin)


# **********************************************************************
# Start execution
# ---------------
# **********************************************************************

def Main():

# Get the selected option if any
    cmd = sys.argv[2].replace("?", "")

# The "applycurrentsettings" command applies the current button settings to the remote
    if cmd == "applycurrentsettings":
        ApplyCurrentSettings(True)

# The "applydefaultsettings" command resets the remote to the ehome driver defaults
    elif cmd == "applydefaultsettings":
        ApplyDefaultSettings(True)

# The "configurebuttons" command opens the settings dialog
    elif cmd == "configurebuttons":
        ConfigureButtonSettings()

# The "defaultbuttons" command restores the default button settings
    elif cmd == "defaultbuttons":
        RestoreDefaultButtonSettings()

# The "editkeyboarddotxml" command edits keyboard.xml
    elif cmd == "editkeyboarddotxml":
        EditKeyboardDotXML()

# The "instructions" command displays the readme file in Notepad
    elif cmd == "instructions":
        ReadInstructions()

# If no command was specified check if the ReportMappingTable registry
# key is not present and warn the user
    else:
        if not CheckRegKey():
            xbmcgui.Dialog().ok(local_string(30300), local_string(30302))

# Finally list the options
    ListOptions()

