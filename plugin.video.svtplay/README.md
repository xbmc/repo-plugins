# XBMC SVT Play addon

With this addon you can stream content from SVT Play (svtplay.se).
The plugin fetches the video URL from the SVT Play website and feeds it to the XBMC video player. HLS (m3u8) is the preferred video format by the plugin.

It requires XBMC 12.0 (frodo) to function.

**Created by nilzen.**

## Explaination of options

* (General) Show subtitles
  * Force programs to start with subtitles enabled. Subtitles can till be toggled on/off by using XBMC's controller shortcuts.
* (General) Show both clips and episodes for programs
  * By default the addon only displays episodes of a program. If this option is enable, the addon will show one section with episodes and one with clips (if available) for the program. If this setting is not enabled clips can only be found by using the search feature.
* (Advanced) Don't use avc1.77.30 streams
  * Forces the addon to choose the stream that supports the highest bandwidth but does not use the avc1.77.30 profile.
* (Advanced) Set bandwidth manually
  * Forces the addon to choose stream according to the set bandwidth. This option can be used to force lower resolution streams on devices with lower bandwidth capacity (i.e mobile devices). This option can only be used if "Don't use avc1.77.30 streams" is disabled.

## Known issues:

* Video playback may stutter on Apple TV2  and Raspberry Pi due to the use of the h264 profile avc1.77.30
  * Use the advanced plugin option "Don't use avc1.77.30 streams" to workaround this issue. This will force SD content only. Note that HD video is not supported on Apple TV 2 anymore due to changes by SVT.
