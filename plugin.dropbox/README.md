# Dropbox for Kodi

Browse your Dropbox in Kodi and play your videos, music and pictures.

- Any number of Dropbox accounts
- Search your Dropbox
- Subtitles stored next to your videos are loaded automatically (same name, e.g. `movie.mkv` and `movie.srt` or `movie.en.srt`)
- Export videos and music to the Kodi library (.strm files)
- Use Dropbox as a source
- Read-only: the add-on never changes or deletes your files

## Signing in

The add-on shows a short code and a QR code. On a phone or computer on the same network as Kodi, open the address shown (https://drive.signinserver.com), enter the code and sign in with Dropbox. The sign-in service is open source: https://github.com/cguZZman/signin-server.

Files are streamed directly between Dropbox and your Kodi device; they never pass through the sign-in service.

## Requirements

Kodi 19 (Matrix) or later, and the Cloud Drive Common Module (`script.module.clouddrive.common`), installed automatically.

## License

GPL-3.0-or-later. This add-on is not affiliated with or endorsed by Dropbox.
