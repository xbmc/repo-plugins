XBMC SVT Play addon
===================

With this addon you can stream content from SVT Play (svtplay.se).

It requires XBMC 12.0 (frodo) to function.

The plugin fetches the video URL from the SVT Play website and feeds it to the XBMC video player. HLS (m3u8) is the preferred video format by the plugin.

Created by nilzen.

Known issues:

* Video playback may stutter on Apple TV2 due to the use of the h264 profile avc1.77.30
  * Use the advanced plugin option "Don't use avc1.77.30 streams" to workaround this issue. Note that HD video is not supported on Apple TV 2 anymore due to changes by SVT.
