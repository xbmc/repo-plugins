# pCloud for Kodi

Browse your pCloud in Kodi and play your videos, music and pictures.

- Any number of pCloud accounts, in the US or in Europe (the add-on finds your account's region when you sign in)
- Search your pCloud
- Subtitles stored next to your videos are loaded automatically (same name, e.g. `movie.mkv` and `movie.srt` or `movie.en.srt`)
- The plot, cast and artwork of Kodi .nfo files and pictures stored next to your videos (`movie.nfo`, `movie-poster.jpg`, `fanart.jpg`) are shown while browsing
- Export videos and music to the Kodi library (.strm files)
- Use pCloud as a source
- Read-only: the add-on never changes or deletes your files

## Signing in

The add-on shows a short code and a QR code. On a phone or computer on the same network as Kodi, open the address shown (https://drive.signinserver.com), enter the code and sign in with pCloud. The sign-in service is open source: https://github.com/cguZZman/signin-server.

pCloud's sign-ins don't expire: after signing in, your Kodi device only talks to pCloud. Files are streamed directly between pCloud and your Kodi device; they never pass through the sign-in service. To end the add-on's access, remove the account in Kodi and revoke the app in your pCloud account settings.

## Requirements

Kodi 19 (Matrix) or later, and the Cloud Drive Common Module (`script.module.clouddrive.common`), installed automatically.

## Installation

* From **[my repository](https://github.com/cguZZman/repository.plugins)**.
* Manually, from a zip of the source code. Install the latest **[common module](https://github.com/cguZZman/script.module.clouddrive.common)** first.

## Help and feedback

Problems: open an issue on [GitHub](https://github.com/cguZZman/plugin.pcloud/issues) and include your [debug log](https://kodi.wiki/view/Log_file/Easy).

## Support this project

The add-ons and the sign-in service are free and open source, and run by one developer for everyone using Google Drive, OneDrive, Dropbox and pCloud in Kodi. Keeping the service online, and the add-ons working as the services change, takes time and money. If you find them useful, you can support the project on **[GitHub Sponsors](https://github.com/sponsors/cguZZman)**, monthly or once.

## License

GPL-3.0-or-later. This add-on is not affiliated with or endorsed by pCloud.
