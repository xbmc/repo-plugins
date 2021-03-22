Introduction
------------
The MCERemote addon for Kodi Dharma (and later versions) is intended to
make it very easy for users to get a Microsoft remote working with
Kodi. However to keep things simple it offers little flexibility. This
document and the associated files are intended for users who want more
control over the customisation, or who are just curious to find out
how it all works.

Note that this document applies exclusively to Windows. On Linux and
OSX remote controllers work through the Lirc interface.

The files included here are (in no particular order):

  MSRemote.reg
  - a registry file to configure the MS remote for use with Kodi

  CreateTestConfig.reg
  - a registry file to install a test configuration. This won't work
  with Kodi. The only purpose of this configuration is to identify any
  additional buttons on MS compatible remotes

  MSDefault.reg
  - a registry file to restore the default configuration set up when a
  Microsoft remote is first connected.

  keyboard.xml
  - an Kodi keymap for buttons that don't have a standard Media Center
  keyboard shortcut, e.g. the four coloured buttons.

  CopyKeyboardDotXML.bat
  - run this script to copy the sample keyboard.xml to your
  userdata\keymaps folder.

  translate.pdf
  - Microsoft document listing all the key codes that can be used in the
  remote registry configuration file.

  ShowKey.exe
  - an applet to identify keystrokes sent by an MCE remote.
  - NB this applet isn't included in the addon because the Kodi addon
    repository doesn't allow binaries. You can get the addon from
    http://Kodimce.sourceforge.net/.


Using a remote with Kodi
------------------------
The big problem with using remote controls on Kodi is that Windows
provides no standard interface for remote ontrols. The way we get round
this is to make the remote control emulate a keyboard i.e. when you
press a button on the remote handset Windows thinks a key has been
pressed on the keyboard.

This may seem a strange way to use a remote control, but in fact many
of the cheaper MCE remotes already work this way. Microsoft have
documented a standard set of keytrokes that remote controls can send.
See http://msdn.microsoft.com/en-us/library/bb189249.aspx if you're
really interested.

The MCERemote addon, and the registry files here, configure the
Microsoft remote so it sends these standard keystrokes. The registry
files will also work with any Microsoft compatible remote that uses the
Microsoft eHome device driver. This includes the HP remote and the
remote included with the Asrock 330HT HTPCs, as well as various other
remotes. See http://wiki.Kodi.org/index.php?title=Remote_Control_Reviews
for some remotes that are known to be compatible with the MS remote.


How it works
------------
On Windows MS compatible remotes are automatically detected as soon as
you connect them, and they use a driver called eHome. If you look in
Device Manager under the Human Interface Devices heading you should see
your remote listed as "Microsoft eHome Infrared Transceiver".

The eHome driver keeps the configuration for the buttons on the remote
in the registry key:

HKEY_LOCAL_MACHINE
 \SYSTEM
  \CurrentControlSet
   \Services
    \HidIr
     \Remotes
      \745a17a0-74d3-11d0-b6fe-00a0c90f57da

The configuration is in a REG_BINARY value called ReportMappingTable.
The MCERemote addon and registry files here work by modifying this
value.

You can install any of the configurations included here just by
double-clicking the .reg file (or by using the addon from within Kodi).

This is probably as far as you need to read if you're just curious. The
following sections go into detail on the format of the
ReportMappingTable value and how to modify it.


The ReportMappingTable value
----------------------------
The ReportMappingTable value is a binary array consisting of rows of 7
bytes. Each row defines one button. The seven bytes in the row are:

Byte  Action
  0   button number (see below)
  1   always 0
  2   always 0
  3   always 0
  4   04 sends a keystroke
  5   key modifier (see below)
  6   keystroke (see below)

Byte 4 can be 01 or 03. These send IR codes not keystrokes and I'm
ignoring these values in this article. I'm only interested in setting
byte 4 to "04" to indicate a keystroke.

Byte 5, the key modifier, specifies if control, shift etc are down when
the key is sent. The value can be:

Byte  Action
  0   No modifier
  1   Control
  2   Shift
  3   Control-Shift
  4   Alt
  5   Control-Alt
  6   Shift-Alt
  7   Control-Shift-Alt
  8   Windows
  9   Control-Windows
  a   Shift-Windows
  b   Control-Shift-Windows
  c   Alt-Windows
  d   Control-Alt-Windows
  e   Shift-Alt-Windows
  f   Control-Shift-Alt-Windows

If you're happy with binary numbers you've probably spotted that bit 0
specifies Control, bit 1 specifies Shift, bit 2 specifies Alt and bit 3
specifies the Windows key.

The keystroke is not an ACSII code or a scan code. It's an arbitrary
code selected by MS. You can find a list of the codes in

http://download.microsoft.com/download/1/6/1/161ba512-40e2-4cc9-843a-923143f3456c/translate.pdf

and I've included a copy with this article in translate.pdf in case the
above link breaks.

So the MCERemote addon and the .reg files work by setting byte 4 to 04
to send a keystroke, and then setting appropriate values for bytes 5
and 6 to specify the keystroke. For example the MCE shortcut for "Play"
is ctrl-shift-P. To specify this keystroke use:

Byte 4 - 04 to specify a keystroke
Byte 5 - 03 to specify ctrl-shift
Byte 6 - 13 to specify the "P" key

and the full line in MSRemote.reg is:

  16,00,00,00,04,03,13,\ ; play - sends ctrl-shift-P

You need to know the button number to put in byte 0 (16 in this
example). The known button numbers are listed in Appendix A. To find
the number for a button you can use the CreateTestConfig.reg config.
See the next section for the details.

Feel free to inspect the .reg files using Notepad; they are all well
commented. Note the files are UNICODE so they may not display properly
in editors that don't support UNICODE.

Finally note that the eHome driver only reads the ReportMappingTable
when it starts i.e. when Windows starts. If you modify
ReportMappingTable you need to restart Windows for your changes to take
effect.


CreateTestConfig.reg
--------------------
The CreateTestConfig.reg config assigns a different keystroke to every
possible button number from 00 to FF. If you need to identify a button
number install this config (and reboot) then run the ShowKey applet,
press the button and see what keystroke ShowKey reports.

For example:

Suppose after installing the CreateTestConfig.reg config you press a
button and Showkey reports:

  KeyID  68 (0x44) - VK_D
  Mod    Ctrl

This is telling you that the button generated a ctrl-D keypress. Open
CreateTestConfig.reg in Notepad and scroll down until you find:

  27,00,00,00,04,01,07,\ ; ctrl-D

This tells you that button number 27 is configured as ctrl-D, and
therefore that the button you pressed is number 27. This is actually
the top left button on the Asrock 330HT remote, which isn't on a
standard MS remote, and this is exactly how I figured out what number
this button was.


Showkey.exe
-----------
When playing around with remote controllers it's useful to see exactly
what the remote controller is sending to Windows. ShowKey is an applet
that records any keystrokes it receives and tells you what they are. It
also gives you the XML you need for using that keystroke in an Kodi
keyboard mapping file. Finally it records any WM_APPCOMMAND
Windows messages it receives. This is likely to be of interest only to
us Windows programmers!


Appendix A: Button numbers
--------------------------
The button numbers I know about are:

  00     0
  01     1
  02     2
  03     3
  04     4
  05     5
  06     6
  07     7
  08     8
  09     9
  0a     Clear
  0b     Enter
  0c     Power
  0d     Windows
  0e     Mute
  0f     Info
  10     vol up
  11     vol down
  12     chan up
  13     chan down
  14     ff
  15     rew
  16     play
  17     record
  18     pause
  19     stop
  1a     next
  1b     prev
  1c     #
  1d     *
  1e     up
  1f     down
  20     left
  21     right
  22     OK (return)
  23     back
  24     DVD menu
  25     Live TV
  26     Guide
  27     Unidentified top left button on Asrock 330HT remote
  47     My Music
  48     Recorded TV
  49     My Pictures
  4A     My Movies
  4E     Print button on HP remote
  50     Radio
  5A     Teletext button
  5B     Red
  5C     Green
  5D     Yellow
  5E     Blue

Every now and then a new MS compatible remote turns up with a new button
not listed above. In that case you can use the CreateTestConfig.reg
configuration to determine the button number.


John Rennie
john.rennie@ratsauce.co.uk
17th October 2010
