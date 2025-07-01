**Ampache-Xbmc-Plugin Overview**

This plugin provides basic connectivity to the Ampache streaming software for XBMC/KODI. It's included in the Kodi Official Repository.

**Installation**

*   For the latest version, download the ZIP file and install it via: System -> AddOns -> Install from ZIP (or AddOns -> Addon Icon -> Install from ZIP in newer Kodi versions).

**Compatibility**

*   Supports Ampache API from 350001 to the latest version.
*   Tested with Kodi 19 and 20.
*   Works with web controls and the Kore app (Kore app has limited support).
*   Tested with the latest stable Ampache server and Nextcloud Music.

**Troubleshooting**

*   **Nextcloud Music Connection:** If you experience connection issues with Nextcloud Music, uncheck the "api_key" box as it uses username/password authentication.
*   **Web Controls Search:** The older search interface may work better with web controls; this can be enabled in the settings.
*   **Plugin Issues After Update (Raspberry Pi):** After updating from an older version, especially on a Raspberry Pi, the plugin may not work due to Kodi addon caching. Reboot your mediacenter. If the problem persists, uninstall and reinstall the plugin.
