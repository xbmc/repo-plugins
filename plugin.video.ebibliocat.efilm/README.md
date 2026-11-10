# eBiblioCat eFilm for Kodi

An unofficial, community-maintained Kodi add-on for the **eBiblioCat** eFilm service. You need a library account eligible for that service. This project is not affiliated with eFilm, the library network, or Team Kodi, and does not provide a subscription or media files.

Add-on ID: `plugin.video.ebibliocat.efilm` · Version: **0.2.3** · License: **GPL-2.0-or-later**

This version prepares the experimental Pi integration for public testing. See [release verification](docs/RELEASE_CHECKLIST.md) for checks performed and device/provider checks still required before describing it as a stable release.

## Install

For automatic updates, prefer the **repository installer ZIP** from a published release, then use **Install from repository → eBiblioCat eFilm repository → Video add-ons**. See [distribution](docs/DISTRIBUTION.md) for the opt-in publishing workflow and how this differs from Kodi’s official catalog.

1. Download `plugin.video.ebibliocat.efilm-0.2.3.zip` from this project's [GitHub Releases](https://github.com/nritsche/plugin.video.ebibliocat.efilm/releases), when a maintainer has published one, or [build it yourself](#development).
2. In Kodi, open **Settings → Add-ons → Install from zip file**, allow installation from unknown sources if Kodi requests it, and select the ZIP. Do not install GitHub's automatic source-code ZIP as a Kodi add-on.
3. Open **Add-ons → Video add-ons → eBiblioCat eFilm**, then **Sign in to eFilm**. Use your eligible library username and password.
4. InputStream Helper is a declared dependency. The add-on checks InputStream Adaptive before borrowing. On distributions that package binary Kodi add-ons separately, install the matching InputStream Adaptive package and enable it under **My add-ons → VideoPlayer InputStream**. DRM titles can require a supported Widevine installation; Helper guides setup when supported by your device.

The code targets **Kodi 19–22 / Python 3.8+**. Pi/Linux has been used for live directory verification and earlier movie playback. Unit tests exercise the version-specific Kodi boundaries, but Windows, Android, macOS, every provider, and every DRM variant are not certified. PlayReady is accepted only on Android with Kodi 21 or newer. FairPlay, embedded web players, and unspecified/unknown DRM are reported as unsupported. Browsing can work even when a particular provider's playback is unavailable.

## Browse and borrow

- **All movies (A–Z)** shows titles exposed by eFilm's movie-catalog API, with previous/next pages and a page/count label.
- **Browse A–Z**, **Search movies**, and **Movies by genre** filter the catalog before pagination. Search matches titles and ignores accents/case.
- **Lists** loads eFilm's current nonempty curated lists. A small static fallback remains available during a directory outage.
- **Series** opens shows, seasons, and individual episodes.
- **Refresh catalog** fetches an updated catalog and returns to its first page. **Clear catalog cache** removes public browsing caches without signing you out.

Selecting a title asks for an available audio/subtitle combination. The add-on checks your current service-side loans before offering **Resume** or **Borrow**. Borrowing always requires confirmation and may consume a loan credit under your library's rules. Expired-loan recovery requires a separate confirmation before creating a new loan. A failed or uncertain borrow request is not automatically repeated: check your loans on eFilm if the outcome cannot be confirmed.

Availability depends on your account, location, age eligibility, provider, device, and the service's current catalog. The add-on does not override those restrictions.

## Privacy and storage

Your password is sent over HTTPS to eFilm during sign-in and is **never saved**. A refresh token and a small loan-ID map are stored in Kodi's add-on profile, `special://profile/addon_data/plugin.video.ebibliocat.efilm/session.json`. Treat that file like a credential. Sign-out removes it and reports filesystem failures rather than pretending to succeed. Session writes are atomic and protected against concurrent add-on invocations; filesystem permissions are restricted where the OS supports them.

Public catalog data is cached in the same profile's `cache/` directory. Movies expire after six hours; other directories after ten minutes. The first movie-catalog fetch takes longer and provides progress/cancellation. An expired cache can be used during transient service failures, with a notification. Refresh starts a new catalog view; the service can add/remove titles between refreshes.

The add-on communicates with eFilm's website and API. There is no add-on analytics service. Debug logs contain operation categories, not passwords, tokens, backend response bodies, or signed playback URLs. Kodi or other installed components may have their own logging behavior; redact logs before sharing them.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Sign-in fails | Account eligibility, correct library credentials, and whether sign-in works on the eBiblioCat website. Password whitespace is preserved. |
| No playback / InputStream message | Install and enable the matching InputStream Adaptive package; complete supported DRM setup using InputStream Helper. |
| Loan rejected | Remaining credits, library lending policy, title availability, region, and account eligibility on eFilm. |
| Borrow outcome uncertain | Check your loans on eFilm before trying again. The add-on will reconcile an existing loan on the next attempt. |
| Catalog is slow or stale | Allow the first download to finish, cancel if needed, or use Refresh catalog. Check network/service availability. |
| Unsupported stream/DRM | Report the provider and your Kodi/platform versions. A supported movie does not establish support for every provider. |
| Local storage error | Available disk space and permissions for the Kodi profile. Do not post `session.json`. |

Report bugs through [GitHub Issues](https://github.com/nritsche/plugin.video.ebibliocat.efilm/issues). Include versions, steps, provider, and a small redacted log excerpt. **Never attach passwords, session files, cookies, authorization headers, or signed stream/license URLs.** See [SECURITY.md](SECURITY.md) for sensitive reports.

## Development

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python scripts/validate_release.py
.venv/bin/python scripts/build_release.py
```

On Windows, use `.venv\Scripts\python` and `.venv\Scripts\ruff`. The output is a deterministic ZIP plus SHA-256 checksum under `dist/`. Packaging uses an explicit runtime allowlist; virtual environments, bytecode, test fixtures, downloaded webpages, and local credentials are excluded. CI runs the same checks and uploads artifacts. [Additional checks](docs/CI.md) include branch coverage, CodeQL, dependency review, Gitleaks, actionlint, and zizmor. A separate [tagged/manual release workflow](docs/DISTRIBUTION.md) can publish a Kodi repository feed; ordinary source pushes do not publish releases.

See [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/ARCHITECTURE.md), and [the release checklist](docs/RELEASE_CHECKLIST.md). Tests use synthetic data and explicit Kodi doubles; they do not sign in, borrow media, or contact the production API.

## Credits and license

This project began as an adaptation of [jqandreu/plugin.video.tv3.cat](https://github.com/jqandreu/plugin.video.tv3.cat). Thanks to jqandreu and the upstream contributors recorded in the retained Git history. Inherited code remains under its applicable GPL terms; the project retains the full [GPL license](LICENSE.txt). The obsolete TV3 service implementation, translations, and branded artwork have been replaced or removed.

The icon is a square, opaque adaptation of the Biblioteques Públiques de Catalunya logo recovered from this project’s Git history. The original logo and the adapted icon master remain in the artwork source directory. The logo and branding belong to their respective owners. The geometric fanart is original project artwork; its source and artwork attribution are in [resources/artwork](resources/artwork/) and [scripts/build_artwork.py](scripts/build_artwork.py). Rebuilding artwork requires Pillow (`python -m pip install 'Pillow>=10.4,<13'`). Service names and logos identify the service being integrated; they do not imply endorsement.
