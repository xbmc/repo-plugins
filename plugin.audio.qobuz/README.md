This is a Qobuz plugin for XBMC
-------------------------------
It enables access to Qobuz music streaming service directly from XBMC (http://xbmc.org)

Main Features : 
---------------

- Show and manage (add/remove/create/rename/delete) playlists
- Show purchased products
- Show recommended albums by genre and type  
- Search by track name, album name and artist name
- Integrate with xbmc gapless play
- Support flac or mp3 play (using settings)
- Show and manage favorites
- musicdb support
- Add/Remove Friends & browse their public playlists
- Browse by genre
- Public playlists

Configuration:
--------------

- Just enter some valid Qobuz credentials using addon settings
notes: 
- you need Hifi subscription to stream flac files or premium subscription to play mp3. 
- create your Qobuz account there : http://www.qobuz.com/inscription (you can use the translate button for your language)

Known Issues:
-------------
- Library scan compilations and albums with guests are not always perfects...

This application uses the Qobuz API but is not certified by Qobuz.
Any use of the API implies your full acceptance of the Qobuz General Terms and Conditions (http://www.qobuz.com/apps/api/QobuzAPI-TermsofUse.pdf)

Audiophile option:
-------------

This is an update to the XBMC/Kodi plug in; Qobuz XBMC.

The update adds a new "Audiophile" option under the add-on settings within the XBMC/Kodi GUI.

When this option is selected via its radio button, each time a user selects either an album or playlist
from within Qobuz XBMC a file named qobuzNow.m3u8 will be written as a playlist
which contains all the urls necessary to play the files from this playlist. 
If the file qobuzNow.m3u8 doesn't exist it will be created. 
The file is written to the users Music directory within his/her home directory of the OS.

The user must have designated a program to open all files of type .m3u8 within his/her operating system.

This should be a program such as foobar2000, HQPlayerDesktop, J River Media center or VLC
since all of these support flac streaming.

As long as a default program which supports flac streaming is chosen in the os by the user
the qobuzNow.m3u8 file will be opened by that program.

Turning the "Audiophile" feature off will cause Qobuz XBMC to revert to its default behaviour of playing Qobuz
streams through XBMC.

Version 1.1.1 Now adds the support for individual tracks to take advantage of this "Audiophile" option.
For this to work you must turn off "Play the next song automatically" under Sytem -> Settings -> Music -> Playback.

Version 1.1.2 Adds choice within Audiophile settings between Gapless and non-Gapless.
Gapless is preferable; but doesn't guarantee long albums/playlists will play to the end.
When Gapless is turned off a slider may be used to adjust the gap in seconds between tracks.
Sufficient time needs to be allowed for each track to load into your player of choice.

The number of seconds needs to be high enough so that tracks are not cut off before they finish playing;
but not so high as to result in unnecessarily long gaps between tracks.

8 seconds seems to work well and is the default. Some experimentation is in order though as each user's systems
and requirements may differ.
