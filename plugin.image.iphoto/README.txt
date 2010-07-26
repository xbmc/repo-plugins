iPhoto plugin for XBMC
======================
This plugin imports an iPhoto library into XBMC.  After importing, you will
see three categories that correspond with their iPhoto counterparts:

* Events
* Albums
* Ratings

Configuration
=============
The plugin needs to know where your AlbumData.xml file is.  If you haven't
explicitly pointed iPhoto to a non-standard library location, the default of
"~/Pictures/iPhoto Library/AlbumData.xml" should work fine.  Otherwise,
please enter in the correct path in the plugin's settings dialog.

The iPhoto plugin can also be configured to ignore certain album types.
It is currently hard-coded to ignore albums of type "Book" and
"Selected Event Album," but you can choose to ignore also:

* Published -- these are albums pushed to your MobileMe Gallery.
* Flagged -- albums flagged in iPhoto's interface.

Both of these album types are ignored by default.

If you select "Auto update library", the plugin will compare the modification
time of your AlbumData.xml with its current database and update the database
automatically on start.  This is disabled by default.

Known Issues
============
* As of 2010/07/21, it's untested under Windows.
* It is unknown if this plugin will work with Apple's Aperature, because I
  don't own a copy.
