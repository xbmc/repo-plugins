MCERemote Addon for Kodi
========================

Introduction
------------
This plugin will customise the Microsoft remote (and compatibles like
the Asrock and HP remotes) for use with Kodi. If you don't have an MS
or compatible remote the plugin will warn you of this. If your remote
isn't MS compatible the addon won't do anything useful, but won't do
any harm either.

The Microsoft remote works pretty well in Kodi without any
customisation needed. Just a few buttons won't work. If you're happy
with this you don't need to use this addon and you need read no
further.

Quick start
-----------
Most people will just want to configure the remote to use the standard
Windows Media Center keyboard shortcuts. In this case just select the
second item in the list "Apply current settings to remote". Exit Kodi
and reboot your PC, and all buttons on the remote will now work with
Kodi. The remote will still work with Windows Media Center as well. If
for any reason you want to back out the changes select the third
option "Apply Windows default settings to remote", exit Kodi and
reboot. This will set the remote back to the way it was before you used
the MCERemote addon.

After you've configured the remote you don't need the addon again and
you can uninstall it. The only reason to leave the addon installed is
if you want to tweak the remote config further.

A note on Windows 10, 7 and Vista: these versions of Windows have a
feature called User Access Control that (very wisely) stops
applications overwriting key bits of the registry. If UAC is on you may
get an error message from the plugin to say it cannot write to the
registry. If this happens try right-clicking on the Kodi shortcut then
choose "Run as administrator", and the plugin should now be able to
write to the registry. You only need to do this once. After you've run
Kodi as administrator and used the plugin you can go back to using Kodi
normally.

Advanced config
---------------

The fourth option in the list "Configure MCERemote settings" allows you
to tweak the config and make any button on the remote send any
keypress.

When you select "Configure MCERemote settings" you see a list of all
the buttons on the remote (NB not all Microsoft remotes have all
buttons). To modify a button mapping select that button and type in the
keypress you want the button to send.

NB if you want the button to use the default Microsoft setting type the
text "mce" (without the quotes). If you don't want the button to be
configured leave the text blank.

The keypress is described as follows:

- use "ctrl-", "shift-", "alt-" and "win-" to set the modifier key. You
  can use any combination of these, for example:
  "ctrl-alt-X" configures the button to send an X keypress with the
  control and alt keys held down. The "win-" modifier is the Windows
  key between the control and alt keys.

- for keypresses that send characters, e.g. "3", "A" or "?", just type
  the character, for example:
  "ctrl-shift-?" sends a ? keystroke with the control and shift keys
  held down.

  Note that Kodi doesn't distinguish between shifted keys, e.g. "/" and
  "?" are the same keystroke because "?" is just "/" with shift down.
  The key text "ctrl-?" and "ctrl-/" send the same keypress and you can
  use either.

- for keypresses that don't send characters, e.g. return and backspace,
  you can use any of the following:

  f1 to f12 - for the function keys
  right, left, down and up - for the arrow keys
  pageup
  pagedown
  return
  backspace
  escape
  tab
  space
  insert
  home
  delete
  end

When you close the Settings dialog be sure to click OK or Kodi will
discard all your changes without warning you!

When you close the Settings dialog you'll be asked if you want to
apply the settings to the remote. You can do this now, or you can
answer "No" then at a later time use the second option "Apply current
settings to remote" to write your settings to the remote.

Finally, if you make a pig's ear of the settings you can use the fifth
option "Restore default MCERemote settings" to restore all the settings
to their default values.

Edit keyboard.xml
-----------------

If you tweak the button settings you might want to write a keyboard.xml
file to make Kodi take whatever action you want on your customised
keypress. The sixth option "Edit keyboard.xml" will edit your
keyboard.xml.

By default your keyboard.xml will be opened in Notepad. If you don't
already have a keyboard.xml you'll be asked if you want to create one.
Answer yes to create a template keyboard.xml that you can modify to your
requirements.

I have written a keymap editor applet but it can't be included in this
addon as the Kodi team (very sensibly) don't allow random executables to
be included in addons. You can download it from:

http://swarchive.ratsauce.co.uk/XBMC/KeyMapEdit.exe

If you download this and place it in any directory that is on the path
the MCERemote addon will use it instead of Notepad. There isn't a manual
for the keymap editor since it hould be pretty obvious how to use it.

John Rennie
16th March 2021
