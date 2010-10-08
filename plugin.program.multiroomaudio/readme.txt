MultiroomAudio & Video Plugin v1.1.2
Author: VortexRotor (teshephe)
Based off of the very fine work of the Launcher Plugin - leo212  (Thanks Lior!!)

The purpose of this plugin is to facilitate the implementation and framework for a True Multi-Room "Syncronized Audio" 
AND Video solution for XBMC.  This is why I have chosen VLC as the program of choice for this effort. Not only does it support
just about all audio and video formats very well but it provides the inherent capability to provide client/server streaming 
syncronization over the local network which means that no more "out-of-phase" audio issues for those of you that have more
than one XBMC box in your home.



The release of Multiroom v1.1.2 plugin includes these New Features: 

- Fixed issue with Shoutcast and other internet streams not playing with plugin activated

- Fixed DVD not playing issue

- Added Install Documentation to xbmc-multiroomaudio site. Located at the following links:
  Linux:
  http://xbmc-multiroom-audio-plugin.googlecode.com/files/MAV%20Plugin%20Installation%20for%20Linux_09302010_v1.1.1.pdf
  Windows:
  http://xbmc-multiroom-audio-plugin.googlecode.com/files/MAV%20Plugin%20Installation%20for%20Windows7-XP_09302010_v1.1.1.pdf




Conceptual Diagram:
                               ________________
                               |  Master XBMC  |<------------------> XMBC Remote (iPhone)  (You can use any app of your choice for control)
                               |  Srvr (main)  |
                               |_______________|  <-------------------| I created a virtual sound out and i pipe all audio out to vlc.
                                       |                                VLC is configured to stream the virtual source to upd://224.0.0.122:1122  (Your choice but VLC is Key!)
                                       |
                                   LAN/Wifi
               ________________________|_______________________                      
               |                       |                       |
           ____|____               ____|____               ____|____
          |  XBMC  |              |  XBMC  |              |  XBMC  |
          |Client 1|              |Client 2|              |Client 3|   <--------------|  All clients have MultiroomAudio plugin and are configured as slaves and source is the master
          |  LRm   |              | Office |              |  Pool  |                     server of udp://@224.0.0.122:1122
          |________|              |________|              |________|


There are alot of different ways to stream audio throughout the home but THE KEY is Syncronized AUDIO!!!!

This plugin requires the following:

XBMC 10 (Dharma) or higher
vlc 1.1.4 or higher (do: sudo add-apt-repository ppa:lucid-bleed/ppa && sudo apt-get update && sudo apt-get install vlc )
For Windows Based machines - some of the scripts utilize powershell v2 - (do: http://www.microsoft.com/downloads/en/details.aspx?FamilyId=60cb5b6c-6532-45e0-ab0f-a94ae9ababf5&displaylang=en and dnld the version you require)
--This is to help fully suppress the background processes (Hopefully this is only a temp requirement) also MAKE SURE that powershell is configured to execute scripts. Here is a link
  to show you how...http://www.tech-recipes.com/rx/2513/powershell_enable_script_support/


Up to date Install/Configuration/Usage/Help can be found @

http://forum.xbmc.org/showthread.php?t=78431

Enjoy! 



Up to date Install / Configuration / Usage / Help can be found @

http://forum.xbmc.org/showthread.php?t=78431

Up to date Install / Configuration / Usage / Help can be found @

http://forum.xbmc.org/showthread.php?t=78431


CHANGLOG:
1.1.2
- Fixed issue with Shoutcast and other internet streams not playing with plugin activated

- Fixed DVD not playing issue

- Added Documentation to xbmc-multiroomaudio site. Located at the following links:
  Linux:
  http://xbmc-multiroom-audio-plugin.googlecode.com/files/MAV%20Plugin%20Installation%20for%20Linux_09302010_v1.1.1.pdf
  Windows:
  http://xbmc-multiroom-audio-plugin.googlecode.com/files/MAV%20Plugin%20Installation%20for%20Windows7-XP_09302010_v1.1.1.pdf

1.1.1
- Streamer IP Input Dialogue - Now set to type "text"

- Fixed default port number for http interface from 8081 to 8080.  The script would fail on intialization because it could not establish connection to 
  XBMC http interface.

1.1.0
- Added DVD Streaming 

- Support for RTP streaming

- SQL Backend

- Autoscan and configuration of Sources

- Background Signalling between Clients and Master via UDP

- Source Auto-Play

- Capability to Stream DVD's

1.0.9
VLC version 1.1.4 required (it's a better release anyhow!!! ;-) )
- Added Option for Master Syncronization (Because of this it is necessary to upgrade to vlc 1.1.4 on linux based systems)

- Added Stop Multiroom-AV to the list (this is a non editable item) It does what it says... it stops all streaming
  (BTW... I add this to my 'favorites' along with my sources)  ;-)

- Added Generate Files to the list for manually generating the scripts needed (this is a non editable item)
  NOTE: You should only run this after you have made a change to the plugin via "addon settings" and requires a restart of XBMC
        for the changes to go into effect.

- Souces in the list now play their respective streams when selected.

- Added Dynamic Playlist function when queuing songs (note: With Linux based xbmc's, that every song has to be individually selected)
  this is due to the continuous play issue that was reported with Linux (XBMC Bug:#10106).

- Fixed Loopback of audio/video when configured for Dedicated Master Streamer.

- Play local i.e. Loopback is now on by default.

- Fixed playercorefactory - set default hideconsole to "TRUE"

- To lessen confusion, sources can be started from the MAV console now "again" - you should still remember to add the .pls locations via
  appropriate Music / Video sections so you can access the source via a remote like "XBMC remote"
  
- Fixed no DVD playing (No DVD streaming at the moment)

- Fixed DOS windows popping up "annoyance" when generating files

- Added more context to the actual plugin (Dialogues, status, and messages) so you can see what is happeing

- Cleaned up some more code.


1.0.8
- Fixed issue for Windows based systems being both client and master

- Continuous "gappless" play added for streaming music/audio files for Windows

- Loopback as Master of playing media added for Windows based systems

- Notification added of starting Streaming Server when in Master mode and Start Streamer on Start is activated via the Addon Settings


1.0.4 - 1.0.7 (BETA) rc45
- Added support for ALL OS's

- Manual On-Demand Streaming of Audio and/or Video from client or master hosts.

- Eliminated need for xdotool and wmctrl application making the plugin OS agnostic.

- Added deletion, renaming of Source generated files when source is renamed or removed

- Added generation of .PLS files for use as shortcuts in user defined folder location via Addon Settings (Misc Setting Section). 
  With this feature, the user can define a folder which can then be added as a Music/Video source respively in the Music 
  and/or Video sections of XBMC

- Playing/Activating are now done via the generated PLS files located in the folder that you choose in the settings.  Once these are created
  you can create a shortcut to the folder location in either the Music and/or Video sections of XBMC using the "add source" in those sections.
  Note: As a result of this change/enhancement, the buttons for the AV sources in the MultiroomAV Plugin now only serve to De-Activate/Kill Streams (in or out)
  when selected and for management purposes such as Renaming, Removing, Editing parameters specific to the source. 

- Fixed path settings for new Dharma release

- Added more functionality to Settings for flexibility and configuration

- Fixed strings.xml for proper display of contexts

- Fixed settings.xml to comply with new GUI standard code conventions

- Corrected language subdirectory name from english to English

- Cleaned up avsources.xml

- Built initial framework for inner Master/Client signalling and communication over local netork and internal to localhost
  that the plugin is running on.

- Added Changelog.txt

Known Issues's (v1.0.7):
- Windows based systems can only be either a client or a master but not both
- "Continuous play" / Streaming of media is currently only supported on Windows based systems. (XBMC Bug:#10106)




1.0.2 - 1.0.4
- found problem with file names(double quotes)
- Cleaned up fixed paths
- Added License file

1.0.1
- strings and list, function building
- added more dynamic functionaly in GUI
- added new default image and plugin icon.png

0.1.0 - 1.0.1
- Lets get started
- change over to XBMC addons support for (XBMC Dharma) and above
- changed revision # scheme (v1.x.x and above support only XBMC Dharma and above releases) 
