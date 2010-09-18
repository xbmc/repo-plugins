MultiroomAudio & Video Plugin v1.0.9
Author: VortexRotor (teshephe)
Based off of the very fine work of the Launcher Plugin - leo212  (Thanks Lior!!)

The purpose of this plugin is to facilitate the implementation and framework for a True Multi-Room "Syncronized Audio" 
AND Video solution for XBMC.  This is why I have chosen VLC as the program of choice for this effort. Not only does it support
just about all audio and video formats very well but it provides the inherent capability to provide client/server streaming 
syncronization over the local network which means that no more "out-of-phase" audio issues for those of you that have more
than one XBMC box in your home.



The release of Multiroom v1.0.9(BETA)r4 plugin includes these New Features: 

- Full OS support (Linux, Windows, OSX)  --- BTW... I use Ubuntu Lucid --- It ROCKS!
- Extended Plugin Settings Dialogue for Initial and Advanced setup of Streaming Server
- Playing/Activating are now done via the generated PLS files located in the folder that you choose in the settings.  Once these are created
  you can create a shortcut to the folder location in either the Music and/or Video sections of XBMC using the "add source" in those sections.



Known Issues's:
- FIXED:  Workaround- Please see changelog for more info 
  Continuous play / Streaming of media is currently only supported on Window based systems. (XBMC Bug:#10106)




All comments, suggestions, help are very welcome.

FYI... at the moment the plugin requires that a master vlc streaming server be configured.  In my home I have the following:

                               ________________
                               |  Master XBMC  |<------------------> XMBC Remote (iPhone)  (You can use any app of your choice for control)
                               |  Srvr (main)  |
                               |_______________|  <-------------------| There are no speakers on this machine - I created a virtual sound out and i pipe all audio out to vlc.
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
--This is to help fully suppress the background processes (Hopefully this is only a temp requirement)



INSTALLATION:

Now Available via XBMC Addons --> Programs Addon Section

This release contains MAJOR changes and you should fully uninstall any prior versions prior to installing this plugin!!!!
INCLUDING THE REMOVAL OF THE PLUGIN DATA IN YOUR USERDATA/addon_data directory.

Basic Setup:
1) Install the plugin via Add-ons directory

2) Configure the plugin by selecting the path to you vlc executable

3) Configure the path for the generated pls files (usually /home/<username> for linux users and C:\Documents and Settings\<username>\My
Documents respectively for Windows users

4) IP or Multicast Address - You can leave this at the default but if you plan on having the abilit of streaming at one point from any box make sure
that each box has a different Multicast IP and Port so that their is no overlap in the broadcast domain. Lets leave it for now at the default of
224.1.1.152

With this setup you could define a source for each on every box and tune into what is playing at any given time from anywhere in the house... starting to see the picture?

5) UDP/TCP Port: As mentioned before, this coincides with the above but lets leave it for now

6) SAP Name - Put a meaningful name with NO spaces for the SAP name

7) if this is the MASTER, then check the Dedicated Streaming Server (you could have all of your boxes set as this) more on that later...

8) Leave Start Streamer on startup "off" for now (Note: You can manually start the Streamer in the plugin "Start Streamer"

9) Again if this is a dedicated Master, then change the Default Video Player to MR-Video_Stream

10) The defaults for the rest should be satifactory

11) Select OK to save the settings.

12) Goto the plugin and select Generate Files

13) Because this is the initial setup of the plugin a full Restart of your machine and XBMC is required.
Note: from here on out, any changes made to the Addon Settings will require a restart of XBMC only so that new playercorefactory.xml file can
be initialized.

Client Specific:
1) After doing the above w/ exception to the Master specific settings... go to the plugin and lets Add a source, call it whatever you gave the above
SAP name of the master like "Livingroom"

2) URL - Define the url of the stream, in this case udp://@224.1.1.152:1152

3) IP address is optional, but put the host ip of the Master here.

This is optional:
Everytime you create a new source a .pls file is generated and stored in the Multiroom-AV folder. In that folder there are two subfolders name VIDEO and AUDIO. Now, what you should do is go into the Music and the Video sections of XBMC under "Files" and do "Add source" to add the VIDEO folder to the Video Section and AUDIO folder to Music. When you get to the point where you give the new item a name, for both instances call it Multiroom-AV and hit OK to save. So, What are we doing here...? Well, by doing this we will have the ability to access the sources via something like the XBMC Remote for iPhone or http.



Up to date Install/Configuration/Usage/Help can be found @

http://forum.xbmc.org/showthread.php?t=78431

Enjoy! 



Up to date Install / Configuration / Usage / Help can be found @

http://forum.xbmc.org/showthread.php?t=78431

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
