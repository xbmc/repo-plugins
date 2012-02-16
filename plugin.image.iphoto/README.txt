iPhoto plugin for XBMC
======================
This plugin imports an iPhoto library into XBMC.  After importing, you will
see categories that correspond with their iPhoto counterparts:

* Events
* Albums
* Faces
* Places
* Keywords
* Ratings

Your iPhoto library can reside locally (on the machine on which you run XBMC)
or can be located on a network share.


Configuration
=============
The plugin needs to know where your AlbumData.xml file is.  If you haven't
explicitly pointed iPhoto to a non-standard library location, the default of
"~/Pictures/iPhoto Library" should work fine.  Otherwise, please enter in the
correct path in the plugin's settings dialog.

The iPhoto plugin can also be configured to ignore certain album types.
It is currently hard-coded to ignore albums of type "Book" and
"Selected Event Album," but you can choose to ignore also:

* Empty -- albums with no pictures.
* Published -- MobileMe Gallery albums.
* Flagged -- albums flagged in iPhoto's interface.
* Keywords -- any photos with these keywords will be hidden.

All of these album types are ignored by default.

If you select "Auto update library", the plugin will compare the modification
time of your AlbumData.xml with its current database and update the database
automatically on start.  This is disabled by default, but is probably what
you want after testing the plugin.

You can also choose the view style for albums if you're using the Confluence
skin.  You may set this to "Image Wrap," "Pic Thumbs," or "Default".  If you
choose "Default," it will preserve whatever view mode you have chosen in XBMC
for each album; otherwise, it will force the view style to the one selected
here.


Referenced and Managed Libraries
================================
iPhoto gives you the option of managing your photos for you, by placing a
copy of them within the library itself, or referencing your originals,
leaving them in their original location on the filesystem.

If your library is managed, you will select "Managed Library" in the plugin
settings (this is the default).

If your library is referenced and you are running XBMC on the same machine
that you use iPhoto, you may also select "Managed Library".

If your library is referenced and resides on a share over the network,
you need to tell the plugin how to access the originals.  If on the
machine you use iPhoto your originals are accessed via, for instance,
"/Volumes/Media/Pictures", they may not be mounted at the same point on
the machine on which you run XBMC.  If this is the case, you will need to
configure the "Local root path to masters" and "Rewrite root path as"
options.


About Places support
====================
If the plugin is configured to support the Places feature of iPhoto, it will
parse the latitude/longitude pairs in iPhoto's database and look up the
corresponding addresses using Google.

If Google reports one or more businesses near the coordinates, the plugin
will use the name of the nearest business for the address to show in the
Places category.  Otherwise, the street address will be used.  In both cases,
the post code and country identifier are appended to the result.

The Places feature also downloads map images to display while you're browsing
the Places category.  Normally, you won't need to do anything to get this
feature, besides enabling it in the plugin configuration.  But, if you import
your library many times within one day, Google may block you from retrieving
map images.  If you receive a map image with a red X over it, the plugin won't
re-download the map until you clear the map image caches.  You can do so by
selecting "Remove cached maps" from the context menu of the Places category.


Translations
============
If you'd like to help translate this plugin to another language, please send
a patch to jingai at floatingpenguins dot com.

If possible, patch against the most recent version at:

  http://github.com/jingai/plugin.image.iphoto


Known Issues
============
* Selecting previous picture sometimes erroneously selects next instead
  See http://trac.xbmc.org/ticket/11826
* Sorting by Date sorts on the file date, not the EXIF date.
  See http://trac.xbmc.org/ticket/10519
* Can only set default view mode in Confluence skin
  See http://trac.xbmc.org/ticket/9952


Assistance
==========
If you need help getting the plugin to work, please visit my thread on the
XBMC forums:

  http://forum.xbmc.org/showthread.php?t=77612

When asking for help or reporting a potential bug, please be prepared to post
your debug log from XBMC and, if you don't mind, your AlbumData.xml from your
iPhoto library.  Remember to remove any private information from both files
before posting them.


Credits
=======
jingai (jingai at floatingpenguins dot com)
Original code:
- Anoop Menon
- Nuka1195
- JMarshal
Icons:
- Firnsy
- brsev (http://brsev.com#licensing)
