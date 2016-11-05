Twitch on Kodi
==================

Watch your favorite gaming streams on Kodi.

FAQ
----------------

* I can't find the Twitch.tv add-on in the Kodi add-on manager!

> Make sure you are using at least Kodi 15 (Isengard), Kodi 16 (Jarvis).

* I'm having issues with the playback of streams (buffering, dropping, stuttering).

> This Addon does not handle any aspect of the playback of Twitch streams (that would be the Kodi Video Player), it simply tells Kodi what to play.
> The Addon does however provide Quality Options which may help if your internet connection / computer specs are below requirements for HD streams.

* I'm experiencing HTTP errors!

> There are various things that can cause this (including Twitch changing things! Which we do try to keep on top of.) but recently, most commonly it is caused by several missing OAUTH entries in the settings section of this addon. Please visit http://www.twitchapps.com/tmi/ and acquire an OAuth Token and insert this to the relevant sections of the addon settings and your HTTP errors may just go away.

What's next?
----------------

Things that need to be done next:

* Implement features based upon user authentication
* Suggestions welcome.

Credit where credit is due.
-------------

Thanks to all the people who contributed to this project:

StateOfTheArt89 (Founder of this project), ccaspers, CDehning, Giacom, grocal, KlingOne, kokarn, Kr0nZ, Liquex, MrSprigster, stuross, ingwinlu, mCzolko, ha107642, G4RL1N, spiffomatic64, stevensmedia, anxdpanic, xsellier, lucabric, dadobt, torstehu, kravone, beastd BtbN, Preovaleo, Blayr, bamberino.

This addon utilizes python-twitch https://github.com/ingwinlu/python-twitch (a project which derived from an early version of this addon and has grown to deserve recognition of its own). Thanks to ingwinlu for his continued work on the project.
