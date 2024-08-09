# 2.x

## [2.1.4](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.1.4) - 2024-08-08

## Changed
- Better UI items management

### Fixed
- InputStream Helper is now called properly ([#50](https://github.com/f-lawe/plugin.video.orange.fr/issues/50))
- Avoid plugin to be run twice on catchup TV videos ([#55](https://github.com/f-lawe/plugin.video.orange.fr/issues/55))

## [2.1.3](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.1.3) - 2024-07-21

### Fixed
- IPTV Manager should now detects Orange TV France from clean install

## [2.1.2](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.1.2) - 2024-07-05

### Changed
- Better timeshift management

## [2.1.1](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.1.1) - 2024-06-23

### Changed
- Use [ABC](https://docs.python.org/3/library/abc.html) for class inheritance
- Move Orange util functions to decicated abstract Orange provider
- Better authenticated request management
- Move caching logic to utils

## [2.1.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.1.0) - 2024-06-21

### Added
- Catchup TV

## [2.0.1](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.0.1) - 2024-06-20

### Changed
- Use Kodi Addon checker from pip package instead of GitHub Actions

## [2.0.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.0.0) - 2024-06-20

### Added
- Ready to publish on Kodi main repository!

## [2.0.0+beta.3](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.0.0+beta.3) - 2024-06-20

### Added
- Proxy settings (not active yet)

## [2.0.0+beta.2](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.0.0+beta.2) - 2024-06-19

### Fixed
- Load channels event if not found in EPG
- Prevent crash on unavailable paid channels

## [2.0.0+beta.1](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v2.0.0+beta.1) - 2024-06-13

### Changed
- Remove provider templates and move methods to utils
- Rename ProviderWrapper to CacheProvider
- Use Ruff for code formatting

### Removed
- Remove service entry point
- Removed basic Kodi integration

### Fixed
- Load data from Orange using new TV token

# 1.x

## [1.5.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.5.0) - 2021-11-22

### Added
- Support for Orange Caraïbe

## [1.4.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.4.0) - 2021-11-21

### Added
- Cache management over get_streams() to prevent Kodi from removing all channels using IPTV Manager

### Fixed
- Provider load from settings

## [1.3.1](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.3.1) - 2021-11-21

### Fixed
- Channel update when no logo available [#14](https://github.com/f-lawe/plugin.video.orange.fr/issues/14)

## [1.3.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.3.0) - 2021-09-11

### Added
- Provider templates now allow to easily support similar backends
- Support for Orange Réunion

## [1.2.2](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.2.2) - 2021-03-23

### Fixed
- Channel groups for basic integration
- Settings translations

## [1.2.1](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.2.1) - 2021-03-14

### Added
- French translations for settings and dialogs

### Changed
- EPG now loaded following TV Guide past and future days settings

### Fixed
- Audio doesn't drop anymore when timeshifting ([issue #612](https://github.com/xbmc/inputstream.adaptive/issues/612))

### Removed
- Remove basic interval setting (now use TV Guide update value)

## [1.2.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.2.0) - 2021-03-12

### Added
- Provider interface to allow multi ISP support
- Support for Orange TV groups

### Changed
- Migrate current Orange integration to the new provider interface
- Update generators to write data from JSON-STREAMS and JSON-EPG formats
- Data files now written into user data folder

## [1.1.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.1.0) - 2021-03-04

### Added
- API calls to Orange now use a randomised user agent string

### Changed
- IPTV Manager integration refactoring
- Multi-days program load logic now embedded directly into Orange API client
- Log helper signature

### Fixed
- Programs responses reduced by half to avoid IncompleteRead error

## [1.0.0](https://github.com/f-lawe/plugin.video.orange.fr/releases/tag/v1.0.0) - 2021-03-01

- Initial release
