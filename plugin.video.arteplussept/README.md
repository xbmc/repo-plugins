# Arte +7

<p align="center">
  <img src="https://github.com/thomas-ernest/plugin.video.arteplussept/blob/master/resources/icon.png" alt="Arte +7 logo">
</p>

## Description

Plugin "plugin.video.arteplussept" to watch Arte content on Kodi (ex XBMC).
Can be used without or with Arte account in order to benefit from a better cross-device experience. For instance starting a video or a serie on the mobile app and resume it on kodi.

### Features

- Browse and watch Arte replays
- Watch Arte live stream
- Search for content on Arte
- Browse or search multi-page content
- Play serie as a playlist or browse serie as a menu.
- Resume a serie from the first not completed episode thanks to Arte history (login required)
- Load serie as a playlist, when watching one of its episode
- Login with your Arte account without storing password on filesystem - only the token 
- Resume videos from where you stopped them (cross device) (login required)
- Manage - view or purge - your Arte history (login required)
- Manage - view, add, delete or purge - your Arte favorites (login required)
- Supported language : FR, EN, DE, PL, IT

### Not (very well) supported
- Multiple language content
- Subtitles
- Geo blocking
- Display of availability / broadcasting dates

For feature requests or reporting issues go [here](https://github.com/thomas-ernest/plugin.video.arteplussept/issues).

# Contributing

Contributions are welcome !
You may look at the [issues](https://github.com/thomas-ernest/plugin.video.arteplussept/issues) or unsupported features above.

## Install the addon locally

Follow the steps bellow depending on your system and software version

### 1. Open the addons folder

Kodi is installed on a different path according to the operating system it is installed on. You can refer to [this page](https://kodi.wiki/view/Kodi_data_folder). Go to $KODI_FOLDER/addons/

### 2. Dowload the addon

In Kodi addons folder
- clone this repository or one of if its forks (preferred)
  - `git clone https://github.com/thomas-ernest/plugin.video.arteplussept.git`
- or download the plugin :
  - [any release](https://github.com/thomas-ernest/plugin.video.arteplussept/releases)
  - [latest commit on master](https://github.com/thomas-ernest/plugin.video.arteplussept/archive/refs/heads/master.zip)

### 3. Install the addon

- If you downloaded a zip, extract the content of the zip in the `addons` folder.
- Make sure that the addon is in folder `plugin.video.arteplussept` (and not `plugin.video.arteplussept-master` if you downloaded the latest commit of master for instance).

For instance for Linux:
```
unzip -x plugin.video.arteplussept-master.zip
mv plugin.video.arteplussept plugin.video.arteplussept-backup OR rm -fr plugin.video.arteplussept
mv plugin.video.arteplussept-master plugin.video.arteplussept
```

### 4. Enjoy

* Done ! The plugin should show up in your video add-ons section.

## Troubleshooting

If you get an issue after a fresh manual installation, you should try
either to restart in order to install dependencies automatically
either to install the dependancies manually. The dependancies are :

* xbmcswift2 (script.module.xbmcswift2)
* requests (script.module.requests)
* dateutil (script.module.dateutil)

They should be in the "addon libraries" section of the official repository.

If you are having issues with the add-on, you can open a issue and join your log file. The log file will contain your system user name and sometimes passwords of services you use in the software, so you may want to sanitize it beforehand. Detailed procedure [here](http://kodi.wiki/view/Log_file/Easy).

## Coding

- Compatible with python 3 only and Kodi Matrix (based on Python 3.8) since version 1.1.5
- Coding guideline :
  - 4 space indentation. No tab.
  - Snake case for variables and methods
  - No parenthesis around keywords like if, elif, for, while...
  - Spaces around = when used in body and script. No space around = when setting method parameters
  - Double quotes for strings used to end_users or logs.
  - Single quotes for dict indices and strings for internal purpose.
  - Object oriented (preferred), not fully applied given original 
  - Pylint guidelines : pydoc for every module and methods...
  - Flake8 guidelines except line length is 100 instead of 79.
- Pylint and Flake8 are run in CI. You might want to install them on your local env.

## Releasing

- For minor version, create a new release branch `release/$MAJOR.$MINOR`. Don't mention bugfix version.
- Add details of the news version in CHANGELOG.md. Do not touch changelog.txt. It is here for legacy purpose.
- Set the version $MAJOR.$MINOR.$BUGFIX (without v) in addon.xml /addon/@version 
- Optionally update highlight changes in addon.xml /addon/extension[@point="xbmc.addon.metadata"]/news. Ensure it counts less than 1500 chars.
- Create a commit with version bump
    - git add addon.xml CHANGELOG.md && git commit -m "Bump version to $MAJOR.$MINOR.$BUGFIX"
- Create and push tag "vMaj.Min.Bug" (with v) in git in order to create a GitHub release and submit [PR to official repo](https://github.com/xbmc/repo-plugins/pulls).
    - git tag -a v$MAJOR.$MINOR.$BUGFIX
    - git push origin --tags
- Done automatically by CI : Create a release in GitHub with name $MAJOR.$MINOR.$BUGFIX (without v). Reuse CHANGELOG.md details as description. https://github.com/thomas-ernest/plugin.video.arteplussept/releases/new
- Done automatically by CI : Submit new version to official Kodi repository
    - One-commit change in matrix branch https://kodi.wiki/view/Submitting_Add-ons
    - Open pull-request to official repo https://github.com/xbmc/repo-plugins/pulls
