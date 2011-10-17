GENERAL

This is a simple XBMC add-on to enable you to listen to more than 200,000 digital recordings of classic computer game and demoscene music. On request the audio is rendered and streamed from a server run by http://www.exotica.org.uk. The search functions in the same way as the search at http://www.modland.com.

"The demoscene is a computer art subculture that specializes in producing demos, which are non-interactive audio-visual presentations that run in real-time on a computer. The main goal of a demo is to show off programming, artistic, and musical skills." /Wikipedia

QUICK SEARCH EXAMPLES

Try the following for some of our favourites.

  * huelsbeck tfmx
  * drax fasttracker
  * pink ahx
  * drax playsid
  * jeroen tel playsid
  * ron klaren
  * hippel sndh
  * hippel coso
  * spaceman protracker
  * muffler
  * 4-mat protracker
  * jeff playsid
  * heatbeat
  * jogeir

USAGE

The search box will match against fields "file name, author, music format, collection"

To make a search enter one or more keywords with an optional prefix of +, - or |. + means the word must appear in the data. - means the word should not appear in the data. If no prefixes are used, the + prefix is assumed so the word must appear in the search results. To match an exact phrase enter the string in quotes. To make this clearer here are some examples

  * apples oranges would match data that contains both the words apples and oranges (in any order)
  * +apples +oranges is equivalent to above.
  * +apples -oranges would match data that contains the word apples but not oranges.
  * |apples |oranges would match data that contains either the word apples or the word oranges.
  * "apples and oranges" would match data that contains the phrase apples and oranges 

You may also use the wildcard * for partial word matching. For example

    * lem* would match any words starting with lem such as lemons or lemmings. 

Note that in boolean mode the wildcard only works appended to a word. You can not use it at the start of a word.

The boolean search can only search on words of 3 characters or more in length, unless searching for a phrase where it can match against phrases containing shorter words (so long as one word is more than 3 characters). 

INSTALL

The add-on is available in the official XBMC repository. 

If you still want to install manually, move the "plugin.audio.modland" directory into your "addons" directory. 

TECHNICAL NOTES

Modland is a very large, and well organised module archive created and maintained by Coma (Daniel Johansson), which contains over 400,000 music modules in more than 300 different formats. The collection is distributed over FTP from the main site and a few mirrors as well as a searchable web interface available on ExoticA. Modland has been online since 2001. 

The following music formants and platforms support streaming via this plugin:

  * Protracker - mod suffix - Originally an Amiga tracker but format used for other platforms
  * Fasttracker 2 - xm suffix - PC music tracker
  * Impulsetracker - it suffix - PC music tracker
  * Playstation Sound Format - psf/minipsf suffix - Music from Playstation games
  * Video Game Music - vgz suffix - various platforms:
      o BBC Micro
      o Colecovision
      o Sega 32X
      o Sega Game Gear
      o Sega Master System
      o Sega Mega CD
      o Sega Megadrive
      o Sega SC-3000
      o Sega SG-1000 
  * Gameboy Sound System - gbs suffix - Music from the Nintendo Gameboy handheld
  * AY Emul - emul suffix - Music from the ZX Spectrum and Amstrad CPC
  * Nintendo SPC - spc suffix - Music from the Super Nintendo console.
  * SNDH - sndh suffix - Music from the Atari ST
  * Various exotic Amiga audio formats (unusual or specialized music formats) including TFMX, Fred,  Soundmon, Sonic Arranger, Hippel and so on.

Streaming is done in realtime from a server in the UK run by buzz [at] exotica.org.uk. There is a limit to the number of tunes that can be streamed. The limit is set to deter script/bot downloading, and should not affect people listening to the tunes in realtime.

More details about the setup can be found at http://www.exotica.org.uk/wiki/Modland


