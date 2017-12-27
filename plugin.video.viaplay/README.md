# Viaplay for Kodi #
This is a Kodi add-on that allows you to stream content from Viaplay in Kodi.

## Disclaimer ##
This add-on is unoffical and is not endorsed or supported by Viaplay in any way. Not all features may work or has been thoroughly tested.

## Dependencies: ##
This add-on is available in the official Kodi repository and all dependencies will be installed automatically when installed from there. However, if you're installing straight from git, please make sure you've got the following modules installed:
 * script.module.requests >= 2.9.1 (http://mirrors.kodi.tv/addons/krypton/script.module.requests/)
 * script.module.iso8601 (http://mirrors.kodi.tv/addons/krypton/script.module.iso8601/)
 * script.module.inputstreamhelper >= 0.2.2 (http://mirrors.kodi.tv/addons/krypton/script.module.inputstreamhelper/)
 
This add-on requires Kodi 17.4 or higher with InputStream Adaptive installed. Kodi 18 is required for Android based devices.

## DRM protected streams ##
Viaplay's content is DRM protected and requires the proprietary decryption module Widevine CDM for playback. You will be prompted to install this if you're attempting to play a stream without the binary installed.
 
Most Android devices have built-in support for Widevine DRM and doesn't require any additional binaries. You can see if your Android device supports Widevine DRM using the [DRM Info](https://play.google.com/store/apps/details?id=com.androidfung.drminfo) app available in Play Store.

## Support ##
Please report any issues or bug reports on the [GitHub Issues](https://github.com/emilsvennesson/kodi-viaplay/issues) page. Remember to include a full, non-cut off Kodi debug log. See the [Kodi wiki page](http://kodi.wiki/view/Log_file/Advanced) for more detailed instructions on how to obtain the log file.

Additional support/discussion about the add-on can be found in the [Viaplay add-on thread](https://forum.kodi.tv/showthread.php?tid=286387).

## License ##
This add-on is licensed under the **GNU GENERAL PUBLIC LICENSE Version 3**. Please see the [LICENSE.txt](LICENSE.txt) file for details.
