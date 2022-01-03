# SomaFM XBMC Plugin

![SomaFM icon](icon.png?raw=true)

This description is a bit outdated. You can simply install this `addon` by browsing the official repositories from within Kodi.

## Installation

Installation currently requires you to know where your `addons` folder is located. Please refer to the [Kodi Wiki article on `userdata`](http://kodi.org/?title=Userdata) to find it. To find the `addons` folder, simply replace every instance of `userdata` in the article with `addons`.

### Git

 1. Change into your `addons` folder
 2. Clone the repository into a new folder `plugin.audio.somafm`
 3. Done

On Unix based operating systems:

```bash
cd ~/kodi/addons/
git clone https://github.com/Soma-FM-Kodi-Add-On/plugin.audio.somafm.git plugin.audio.somafm
```

### ZIP

Unfortunately, installing from a zip archive is not a lot easier

 1. [Download the zip archive from GitHub](https://github.com/Soma-FM-Kodi-Add-On/plugin.audio.somafm/archive/master.zip)
 2. Extract the contents
 3. Rename the resulting folder `xbmc-somafm-master` to `plugin.audio.somafm`
 4. Move the folder to your `addons` folder

On Unix based operating systems:

```bash
wget --content-disposition https://github.com/Soma-FM-Kodi-Add-On/plugin.audio.somafm/archive/master.zip
unzip xbmc-somafm-master.zip
mv xbmc-somafm-master/ plugin.audio.somafm
mv plugin.audio.somafm/ ~/kodi/addons/
```

![SomaFM fanart](fanart.jpg?raw=true)

Lone DJ photo ©2000 Merin McDonell. Used with permission.
