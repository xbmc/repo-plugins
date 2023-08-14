Changelog also available in file ./addon.xml xpath /addon/extension/news following Kodi guidelines https://kodi.wiki/view/Add-on_structure#changelog.txt

v1.2.1 (2023-8-12)
- Add context menu to view collection as menu instead of playlist
- Set resume point to 0 when video was fully watched. Avoid crash when playing seq of watched videos in playlist.

v1.2.0 (2023-7-26)
- Manage collections TV_SERIES and MAGAZINE as video playlist
- Add a context menu item to purge favorites
- Add a context menu item to mark as video as watched in Arte

v1.1.10 (2023-5-28)
- Bugfix to display favorites and last vieweds following id change in Arte

v1.1.9 (2023-4-18)
- Improve security and performance by caching token to limit authentication requests
- Fallback on clip, when stream is not available anymore. Same feature as on Arte mobile. For favorite content.
- Clean-up and lint code
- Add CI with Pylint and Kodi addon submitter

v1.1.8 (2023-2-17)
- Improve synchronization of playback progress with Arte TV
    - Synchronize progress every minute
    - Fix missing synchronization when playback ends
    - Enable Resume from beginning (on top of synchronized progress point)
- Improve display of collection item in home page
    - Before : rely on old sub category, creating additional menu with a dead entry
    - After : rely on cached category, collection videos directly poulated from home page zone
- Add label in notification when manipulating favorites
- Fix plural for Polish
- Non-functional code clean-up

v1.1.7 (2023-2-14)
- Add feature to purge my history thanks to action in context menu of my history
- Move addon.py to root following Kodi recommendations
- Move back change log fron addon.xml //news to CHANGELOG.md because news is limited to 1500 characters
- Fix translation in English for Successfully removeD from favorite
- Log message instead of notify user, when user or password are not confiugred, while using synched player

v1.1.6 (2023-2-11)
- Fixed playback progress / resume point retrieved from Arte TV
- Added synchronisation of playback progress with Arte TV when video playback paused, stopped or crashed
- Fixed error when live or viewed streams are not available
- Optimize navigation when cancelling or doing empty search - Avoid display empty page
- Fixed client from web to tv for more accurate content - web content contains more links not browsable in Kodi
- Factorized changelog - Keep them only in addon.xml //news following Kodi's recommendations

v1.1.5 (2023-1-30)
- Populate root menu from Arte TV API instead of HBB TV. Still play video from HBB TV.
- Manage favorites in Arte profile from context menu
- Added Search in root menu

v1.1.4 (2023-1-14)
- Added Live stream in root menu
- Got Magazines A-Z content from Arte TV instead of HBB TV API.
- Fixed empty categories - discrepencies with Arte TV - Bug #79

v1.1.3 (2022-12-29)
- Added Polish translation
- Added My list and My history content from Arte TV profile

v1.1.2 (2021-06-27)
- better date / locale handling and prevent crash when http error

v1.1.1
- minor python 3 fixes and code improvements (from Kodi Travis CI)

v1.1.0
- API fixes
- Added add-on option to select video stream (language, subtitles...)

v1.0.2
- weekly browse
- bugfix (settings parsing #54)

v1.0.1
- major bug hotfix

v1.0.0
- brand new version
- support for new arte api