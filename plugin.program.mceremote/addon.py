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

import xbmcgui
import mceremote

# **********************************************************************
# Start execution
# ---------------
# **********************************************************************

# Check if we are running on Windows and display an error if not
if sys.platform != "win32":
    xbmcgui.Dialog().ok(mceremote.local_string(30300), mceremote.local_string(30301))

# We're on Windows
else:
    mceremote.Main()
