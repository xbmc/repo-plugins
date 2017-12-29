# C More for Kodi #
This is a Kodi add-on that allows you to stream content from C More in Kodi.

## Disclaimer ##
This add-on is unoffical and is not endorsed or supported by C More Entertainment in any way. Not all features may work or has been thoroughly tested.

## Dependencies: ##
 * script.module.requests >= 2.9.1 (http://mirrors.kodi.tv/addons/krypton/script.module.requests/)
 * script.module.inputstreamhelper >= 0.2.2 (http://mirrors.kodi.tv/addons/krypton/script.module.inputstreamhelper/)
 
This add-on requires Kodi 17.4 or higher with InputStream Adaptive installed. Kodi 18 is required for Android based devices and for subtitles support.

## DRM protected streams ##
Most of C More's content is DRM protected and requires the proprietary decryption module Widevine CDM for playback. You will be prompted to install this if you're attempting to play a stream without the binary installed.

Most Android devices have built-in support for Widevine DRM and doesn't require any additional binaries. You can see if your Android device supports Widevine DRM by using the [DRM Info](https://play.google.com/store/apps/details?id=com.androidfung.drminfo) app available in Play Store.

## Support ##
Please report any issues or bug reports on the [GitHub Issues](https://github.com/emilsvennesson/kodi-cmore/issues) page. Remember to include a full, non-cut off Kodi debug log. See the [Kodi wiki page](http://kodi.wiki/view/Log_file/Advanced) for more detailed instructions on how to obtain the log file.

## License ##
This add-on is licensed under the **The MIT License**. Please see the [LICENSE.txt](LICENSE.txt) file for details.
