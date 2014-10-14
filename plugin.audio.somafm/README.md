SomaFM XBMC Plugin
==================

Installation
------------

Installation currently requires you to know where your `addons` folder is located. Please refer to
the [XBMC Wiki article on `userdata`](http://wiki.xbmc.org/?title=Userdata) to find it. To find the
`addons` folder, simply replace every instance of `userdata` in the article with `addons`.

### Git

 1. Change into your `addons` folder
 2. Clone the repository into a new folder `plugin.audio.somafm`
 3. Done

On Linux and possibly Mac OSX

    cd ~/xbmc/addons/
    git clone https://github.com/nils-werner/xbmc-somafm.git plugin.audio.somafm

### ZIP

Unfortunately, installing from a ZIP-file is not a lot easier

 1. [Download the ZIP Archive from GitHub](https://github.com/nils-werner/xbmc-somafm/archive/master.zip)
 2. Extract the contents
 3. Rename the resulting folder `xbmc-somafm-master` to `plugin.audio.somafm`
 4. Move the folder to your `addons` folder

Again on Linux and possibly Mac OSX

    wget --content-disposition https://github.com/nils-werner/xbmc-somafm/archive/master.zip
    unzip xbmc-somafm-master.zip 
    mv xbmc-somafm-master/ plugin.audio.somafm
    mv plugin.audio.somafm/ ~/xbmc/addons/