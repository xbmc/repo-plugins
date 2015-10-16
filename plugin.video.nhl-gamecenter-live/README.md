xbmc-nhl-gamecenter
===================

XBMC-NHL-GameCenter is a video plugin for Kodi (formerly known as XBMC) that allows you to watch NHL GameCenter videos. [View the discussion thread here.](http://forum.kodi.tv/showthread.php?tid=207178)

This plugin requires a valid subscription to NHL GameCenter, and is subject to local blackouts imposed by the NHL.

**THIS PLUGIN IS COMPLETELY UNOFFICIAL AND IS NOT ENDORSED BY THE NHL OR ANYONE ASSOCIATED WITH THE NHL.**

Notable features:
-----------------

* Watch the following game types in high quality (up to 5000kbps and 60fps):
    - Live games (including the ability to rewind a live game to the beginning of the game)
    - Recently live and upcoming games
    - Archived games
    - Condensed games
    - Game highlights
    - French streams (when available)
* Each game displays a unique matchup image showing the logos of the two teams that are playing.
* Ability to specify an HTTP/HTTPS proxy to be used only by this add-on.
* The list of games clearly shows which games have yet to start, are in progress, and have ended.
* The list of games optionally shows the current score for the game.
* Hassle-free operation. You should only have to concern yourself with how your favorite team is playing. Leave the implementation details to me. I will consider it a personal failure if I ever have to give troubleshooting instructions that begin with something to the effect of "try deleting your cookies and see if that fixes it."

Am I missing a feature that you're just dying to have?  Let me know what it is, and I'll consider implementing it!

Screenshots:
------------

[Screenshots can be viewed here.](https://github.com/timewasted/repository.timewasted-files/tree/master/screenshots/plugin.video.xbmc-nhl-gamecenter)

Installation:
-------------

[Download the repository](https://github.com/timewasted/repository.timewasted-files/raw/master/repository.timewasted.zip), and then use the *Install from zip file* option for installing add-ons. Install *NHL GameCenter* from the Timewasted repository.

Limitations:
------------

Rewinding a live game to the beginning of the game has rough edges that can't easily (if at all) be worked around within the context of a plugin for Kodi. First, skipping around in a rewound stream works best in Helix due to the updated version of ffmpeg. It will work in Gotham, but there's no guarantee that you'll be able to skip around in the stream. Second, the rewound stream is presented as a playlist that is 4+ hours long, regardless of the actual game status. There is no indication of when you will catch up to the live stream, and if/when you do, you will simply be kicked back to the menu system.

License:
--------
```
Copyright (c) 2014, Ryan Rogers
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
