# Advanced MAME Launcher #

*Advanced MAME Launcher* is an advanced MAME front end for Kodi media center. AML has support for both
MAME archade machines and Software Lists. AML supports `Merged`, `Split` and `Non-merged` ROM sets and
has the ability to fully audit your ROM and CHD collection.

## Getting Started guide and Documentation ##

A *Getting Started* guide with installation instructions and more information about AML can be 
found in the [Advanced MAME Launcher thread] in the Kodi forum. Feel free to ask there any 
AML-related question you may have.

You may also find some documentation is in the [Advanced MAME Launcher wiki] in Github. Note that currently
this guide is far from complete and I will try to improve it soon.

[Advanced MAME Launcher thread]: https://forum.kodi.tv/showthread.php?tid=304186

[Advanced MAME Launcher wiki]: https://github.com/Wintermute0110/plugin.program.AML.dev/wiki

## Screenshot gallery ##

All the screenshots have been taken using the skin [Estuary AEL MOD](https://forum.kodi.tv/showthread.php?tid=287826&pid=2398922#pid2398922). Kodi skins may not show all AML metadata and artwork.

**Addon main window**

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_01_main_window.jpg)

**Browsing MAME machines**

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_02_MAME_pclone_list.jpg)

**Browsing Software Lists**

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_03_SL_pclone_list.jpg)

**Fanart and 3D Box generation**

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_04_MAME_fanart.jpg)

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_05_SL_fanart.jpg)

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_06_MAME_3dbox.jpg)

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_07_SL_3dbox.jpg)

**Audit and ROM browser**

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_09_MAME_ROMs_db.jpg)

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_10_MAME_Audit_db.jpg)

![](https://raw.githubusercontent.com/Wintermute0110/plugin.program.AML.dev/master/media/shot_11_MAME_Audit_machine.jpg)

## Installing the latest released version ##

Advanced MAME Launcher is now available in the
[Kodi Official Addon repository](https://kodi.tv/addon/plugins-program-add-ons/advanced-mame-launcher-0).
To install the latests release AML version follow the instructions in the
[Kodi wiki](https://kodi.wiki/view/Add-on_manager). Advanced MAME Launcher is inside the
category **Program add-ons**.

## Installing the latest development version ##

The development version of AML is a separate addon from the stable version. Both can be
coinstalled on the same Kodi machine and won't interfere with each other. In other words,
changing settings in the development version will not affect your stable AML installation.

The name of the AML stable version is **Advanced MAME Launcher** and the name of the
development version is **Advanced MAME Launcher (dev version)**.

**IMPORTANT** If you are using Kodi Matrix use the `master` branch. If you are using Kodi Krypton or Kodi Leia use the `python2` branch. To change the branch use the drop-down button on top of the page. The default branch is `master`.

It is important that you follow this instructions or the Advanced MAME Launcher development
version won't work well.

  1) In this page click on the green button `Clone or Download` --> `Download ZIP`

  2) Uncompress this ZIP file. This will create a folder named `plugin.program.AML.dev-master` or `plugin.program.AML.dev-python2`

  3) Rename that folder to `plugin.program.AML.dev`.

  4) Compress that folder again into a ZIP file named `plugin.program.AML.dev.zip`.

  5) In Kodi, use that ZIP file (and not the original one) to install the addon.

  6) If you get a warning message dialog `For security, installation of add-ons from
     unknown sources is disabled.` then click on `Settings` button and then activate
     the option `Unknown sources`.
