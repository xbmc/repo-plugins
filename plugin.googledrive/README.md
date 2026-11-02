# Google Drive for Kodi

> **Google is blocking new sign-ins until it verifies the add-on.**
> On October 31, 2026, accounts added before the new sign-in server (drive-login.herokuapp.com) stopped working: they were linked to the add-on's old Google app, which has been retired.
> * Until Google verifies the add-on's new app, it shows "This app is blocked" to new users of that app. We're working on the verification and will announce it in [this issue](https://github.com/cguZZman/plugin.googledrive/issues/357).
> * The verification requires a security review that costs $675 every year. If you'd like to help make it happen, you can support the project on **[GitHub Sponsors](https://github.com/sponsors/cguZZman)**.
> * Meanwhile, you can sign in with a Google app of your own: see **[Signing in with your own Google app](#signing-in-with-your-own-google-app)** (version 1.6.13 or later, about 10 minutes).
> * Accounts already added through https://drive.signinserver.com keep working; you don't need to do anything.
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
* Optionally, sign in with your own Google Cloud app

This program is not affiliated with or sponsored by Google.

## Video quality

Videos play in their original quality: Google's API only gives access to the original file, not the lower-quality versions the Drive website plays. If a video stutters on a slow connection:
* Give Kodi a larger buffer: raise **Memory size** in **Settings → Services → Caching** (Kodi 21 or later, Advanced settings level). On Kodi 19 and 20 the same settings go in advancedsettings.xml. See [Kodi's caching settings](https://kodi.wiki/view/Settings/Services/Caching).
* Or store a lower-bitrate copy of the video in your Drive, made with a converter such as [HandBrake](https://handbrake.fr).

## Signing in with your own Google app

Instead of the add-on's Google app, you can sign in with one of your own, created in a Google Cloud project. Your sign-in then doesn't depend on the add-on's app: use it while Google blocks new sign-ins to the add-on's app, or if you prefer your own. It's free, takes about 10 minutes, and needs Google Drive 1.6.13 or later.

1. Open the [Google Cloud console](https://console.cloud.google.com) with any Google account and create a project (for example "My Kodi").
2. In **APIs & Services → Library**, find **Google Drive API** and select **Enable**.
3. Open **[Google Auth Platform](https://console.cloud.google.com/auth/overview)** and select **Get started**:
   * App name: anything, for example "My Kodi". User support email: yours.
   * Audience: **External**. Contact information: your email. Accept the policy and select **Create**.
4. In **Branding**, fill in and save:
   * Application home page: `https://drive.signinserver.com`
   * Application privacy policy link: `https://drive.signinserver.com/privacypolicy`
   * Authorized domains: `signinserver.com`
   * Leave the logo empty: an app with a logo needs Google's verification.
5. In **Data access**, select **Add or remove scopes**, add `https://www.googleapis.com/auth/drive.readonly` under **Manually add scopes**, and save.
6. In **Audience**, select **Publish app** and confirm, so the status is **In production**. Don't submit it for verification. (In **Testing**, Google ends your sign-in every 7 days.)
7. In **Clients**, select **Create client**:
   * Application type: **Web application**.
   * Authorized redirect URIs: `https://drive.signinserver.com/callback`
   * Select **Create**, and copy the **Client ID** and **Client secret**, or download the JSON: Google doesn't show the secret again. A new client can take a few minutes to start working.
8. In Kodi, add an account in the Google Drive add-on. On https://drive.signinserver.com, enter the code, open **Google Drive: sign in with your own Google app (advanced)**, paste the client ID and secret, and select **Continue**.
9. Google says it hasn't verified the app: it's yours. Select **Advanced**, then **Go to (your app's name)**, and allow access.

Kodi keeps your app's client ID and secret with the account and renews the sign-in with Google directly, without the sign-in server. The sign-in server only holds them in memory during the sign-in, and never stores them. You can use the same app on all your Kodi devices. Removing the account in Kodi can revoke its access; deleting the project ends it for every device.

## Installation

* From the **Kodi Add-on repository** (Add-ons → Install from repository → Kodi Add-on repository → Video add-ons).
* From **[my repository](https://github.com/cguZZman/repository.plugins)**, which gets new versions first.
* Manually, from a zip of the source code. Install the latest **[common module](https://github.com/cguZZman/script.module.clouddrive.common)** first.

### Getting updates from my repository

New versions reach [my repository](https://github.com/cguZZman/repository.plugins) first, and the official Kodi repository after Team Kodi's review. Kodi 19 and later only updates add-ons that are also in the official repository from there. To get my repository's versions as soon as they're out, set **Settings → System → Add-ons → Update official add-ons from → Any repositories**.

## Support this project

The add-ons and the sign-in service are free and open source, and run by one developer for everyone using Google Drive, OneDrive and Dropbox in Kodi. Keeping the service online, and the add-ons working as the services change, takes time and money. This year's goal is **$840**: the security review Google requires every year so the Google Drive add-on can keep signing in ($675), plus domains, hosting, payment fees and taxes. If you find them useful, you can support the project on **[GitHub Sponsors](https://github.com/sponsors/cguZZman)**, monthly or once.
