GENERAL

This is a simple XBMC add-on to generate random waltz theme following Mozart's Musical Dice Game (Musikalisches Würfelspiel). 

Each waltz consist of two parts: a minuet (16 bars of music) and a trio (another 16 bars). Mozart wrote a total of 272 pieces which get randomly combined to produce an unique waltz every time (originally combination was obtained using dice roll, hence the name).

Python coding: Assen Totin, <assen.totin@gmail.com> with little help from some friends :-)

MIDI processing based on Will Ware's "MIDI classes and parser in Python", 2001 - originally published at alt.sources newsgroup, web access: http://groups.google.com/group/alt.sources/msg/0c5fc523e050c35e

Original score and tables of combination: Wolfgang Amadeus Mozart (1756-1791).

WAV files found at Princeton University's public FTP, ftp://ftp.cs.princeton.edu/pub/cs126/mozart/mozart.jar 

MIDI files originally found at Steven Goodwin's midilib, http://www.bluedust.dontexist.com/midilib; further processed to remove unneeded gaps in the beginning of each file which makes on-the-fly concatenation easier. 


INSTALL

To install in XBMC, get it from the official add-ons repository.

To install manually, move the "plugin.audio.mozart" directory into your "addons" directory.


NOTES

This implementation has two modes of operation: 

- Upon run, it will check whether MIDI support is available on the host system
- If MIDI playback is available, MIDI files will be used. Necessary MIDI files are supplied with the add-on.
- If MIDI playback is not available, WAV files will be used instead. Necessary WAV files will be downloaded from the Internet upon the first run and cached locally. 

The rationale behind such approach is the following: while WAV files are compatible with all ports of XBMC, they have the disadvantage of being ~35 MB, which means it takes some time to initially download them. On the other hand, MIDI files are really tiny (all 272 take less than 100 KB), but currently (as of XBMC 11.0 Eden) MIDI playback requires some user action to set it up (e.g., on Linux one have to manually install a soundfont of approx 100 MB, which not all users decide to do).  

