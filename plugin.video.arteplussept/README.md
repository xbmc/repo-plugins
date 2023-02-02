# plugin.video.arteplussept

Plugin Kodi (ex XBMC) permettant de voir les vidéos disponibles sur Arte +7

For feature requests or reporting issues go [here](https://github.com/thomas-ernest/plugin.video.arteplussept/issues).

Contributions are welcome !

# Installation

You can either :

1. Install a stable version directly from the official Kodi repositories (gotham or helix)
2. Install the latest dev version by reading the "Manual installation" chapter


# Manual installation

Download the plugin [here](https://github.com/thomas-ernest/plugin.video.arteplussept/archive/refs/heads/master.zip)

Then follow the steps bellow depending on your system and software version

## 1. Open the addons folder

### Windows

* For Kodi : Press `Windows + R` and type in `%APPDATA%\kodi\addons`
* For XBMC : Press `Windows + R` and type in `%APPDATA%\XBMC\addons`

### Linux

* For Kodi : Open the `~/.kodi/addons` folder
* For XBMC : Open the `~/.xbmc/addons` folder

### OSX

* For Kodi : Open the `/Users/<your_user_name>/Library/Application Support/Kodi/addons` folder
* For XBMC : Open the `/Users/<your_user_name>/Library/Application Support/XBMC/addons` folder

## 2. Install the add-on

* Extract the content of the zip in the `addons` folder
* Rename the extracted directory from `plugin.video.arteplussept-master` to `plugin.video.arteplussept`

### Linux

* unzip -x plugin.video.arteplussept-master.zip
* mv plugin.video.arteplussept plugin.video.arteplussept-backup OR rm -fr plugin.video.arteplussept
* mv plugin.video.arteplussept-master plugin.video.arteplussept

## 3. Enjoy

* Done ! The plugin should show up in your video add-ons section.

# Troubleshooting

If you get an issue after a fresh manual installation, you should try
either to restart in order to install dependencies automatically
either to install the dependancies manually. The dependancies are :

* xbmcswift2 (script.module.xbmcswift2)
* requests (script.module.requests)
* dateutil (script.module.dateutil)

They should be in the "addon libraries" section of the official repository.

If you are having issues with the add-on, you can open a issue ticket and join your log file. The log file will contain your system user name and sometimes passwords of services you use in the software, so you may want to sanitize it beforehand. Detailed procedure [here](http://kodi.wiki/view/Log_file/Easy).
