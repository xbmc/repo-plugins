# Dropbox for Kodi

Browse your Dropbox in Kodi and play your videos, music and pictures.

- Any number of Dropbox accounts
- Search your Dropbox
- Shared with me: folders and files others share with you, even those you haven't added to your Dropbox
- Subtitles stored next to your videos are loaded automatically (same name, e.g. `movie.mkv` and `movie.srt` or `movie.en.srt`)
- The plot, cast and artwork of Kodi .nfo files and pictures stored next to your videos (`movie.nfo`, `movie-poster.jpg`, `fanart.jpg`) are shown while browsing
- Export videos and music to the Kodi library (.strm files)
- Use Dropbox as a source
- Read-only: the add-on never changes or deletes your files

## Signing in

The add-on shows a short code and a QR code. On a phone or computer on the same network as Kodi, open the address shown (https://drive.signinserver.com), enter the code and sign in with Dropbox. The sign-in service is open source: https://github.com/cguZZman/signin-server.

Files are streamed directly between Dropbox and your Kodi device; they never pass through the sign-in service.

## Requirements

Kodi 19 (Matrix) or later, and the Cloud Drive Common Module (`script.module.clouddrive.common`), installed automatically.

## Installation

* From the **Kodi Add-on repository** (Add-ons → Install from repository → Kodi Add-on repository → Video add-ons).
* From **[my repository](https://github.com/cguZZman/repository.plugins)**, which gets new versions first.
* Manually, from a zip of the source code. Install the latest **[common module](https://github.com/cguZZman/script.module.clouddrive.common)** first.

### Getting updates from my repository

New versions reach [my repository](https://github.com/cguZZman/repository.plugins) first, and the official Kodi repository after Team Kodi's review. Kodi 19 and later only updates add-ons that are also in the official repository from there. To get my repository's versions as soon as they're out, set **Settings → System → Add-ons → Update official add-ons from → Any repositories**.

## Help and feedback

Questions and discussion: the add-on's [Kodi forum thread](https://forum.kodi.tv/showthread.php?tid=389080). Problems: open an issue on [GitHub](https://github.com/cguZZman/plugin.dropbox/issues) and include your [debug log](https://kodi.wiki/view/Log_file/Easy).

## Support this project

The add-ons and the sign-in service are free and open source, and run by one developer for everyone using Google Drive, OneDrive and Dropbox in Kodi. Keeping the service online, and the add-ons working as the services change, takes time and money. This year's goal is **$840**: the security review Google requires every year so the Google Drive add-on can keep signing in ($675), plus domains, hosting, payment fees and taxes. If you find them useful, you can support the project on **[GitHub Sponsors](https://github.com/sponsors/cguZZman)**, monthly or once.

## License

GPL-3.0-or-later. This add-on is not affiliated with or endorsed by Dropbox.
