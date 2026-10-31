# Google Drive for Kodi

> **The old sign-in server closes on October 30, 2026.** `drive-login.herokuapp.com` stops working that day; the add-ons now sign in at **https://drive.signinserver.com**.
> * **Kodi 19 or later:** if the add-on stops working, update it (Add-ons > My add-ons > Video add-ons > Google Drive > Update). Your accounts keep working; you won't need to sign in again.
> * **Kodi 17 or 18:** no longer supported. Please update Kodi to version 19 or later.

Play the videos, music and pictures in your Google Drive on Kodi.
* Any number of accounts
* My Drive, shared drives, Shared with me and Starred
* Search your Drive
* Video and music playback with seeking, and video listings with thumbnails
* Subtitles stored next to a video, with the same name (for example `movie.mkv` and `movie.srt`), are loaded automatically
* The plot, cast and artwork of Kodi .nfo files and pictures stored next to a video (`movie.nfo`, `movie-poster.jpg`, `fanart.jpg`) are shown while browsing
* Pictures full screen, as a slideshow, or as an auto-refreshed slideshow that picks up new pictures
* Export videos and music to the Kodi library (.strm files)
* Use Google Drive as a source in Kodi's file manager (add `http://localhost:8587/source/` as a source)
* Read-only: the add-on never changes or deletes your files
* Sign in from your phone or computer with a short code shown in Kodi: your password is only entered on Google's pages

This program is not affiliated with or sponsored by Google.

## Video quality

Videos play in their original quality: Google's API only gives access to the original file, not the lower-quality versions the Drive website plays. If a video stutters on a slow connection:
* Give Kodi a larger buffer: raise **Memory size** in **Settings → Services → Caching** (Kodi 21 or later, Advanced settings level). On Kodi 19 and 20 the same settings go in advancedsettings.xml. See [Kodi's caching settings](https://kodi.wiki/view/Settings/Services/Caching).
* Or store a lower-bitrate copy of the video in your Drive, made with a converter such as [HandBrake](https://handbrake.fr).

## Installation

* From the **Kodi Add-on repository** (Add-ons → Install from repository → Kodi Add-on repository → Video add-ons).
* From **[my repository](https://github.com/cguZZman/repository.plugins)**, which gets new versions first.
* Manually, from a zip of the source code. Install the latest **[common module](https://github.com/cguZZman/script.module.clouddrive.common)** first.

### Getting updates from my repository

New versions reach [my repository](https://github.com/cguZZman/repository.plugins) first, and the official Kodi repository after Team Kodi's review. Kodi 19 and later only updates add-ons that are also in the official repository from there. To get my repository's versions as soon as they're out, set **Settings → System → Add-ons → Update official add-ons from → Any repositories**.

## Support this project

The add-ons and the sign-in service are free and open source, and run by one developer for everyone using Google Drive, OneDrive and Dropbox in Kodi. Keeping the service online, and the add-ons working as the services change, takes time and money. This year's goal is **$840**: the security review Google requires every year so the Google Drive add-on can keep signing in ($675), plus domains, hosting, payment fees and taxes. If you find them useful, you can support the project on **[GitHub Sponsors](https://github.com/sponsors/cguZZman)**, monthly or once.
