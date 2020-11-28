[Kodi Documentation (codedocs)](https://codedocs.xyz/xbmc/xbmc/)

[RA buildbot cores](https://buildbot.libretro.com/nightly/)

[RA MAME 2003 core controls](https://docs.libretro.com/library/mame_2003/)

MAME 2003 Plus RA core write the file `mame2003-plus.xml` in `SAVES_DIR/mame2003-plus/` directory.

## AML and Python 2 (Kodi Krypton and Leia) / Python 3 (Kodi Matrix)

 * AML releases `0.9.x` and `0.10.x` will be **Python 2** for Kodi Krypton and Kodi Leia. **Python 2** code will be in branch `python2`.

 * AML releases `1.x.y` will be **Pyhton 3** for Kodi Matrix and up. **Pyhton 3** code will be in branch `master`.

 * From now on (August 2020), focus will be on release `1.x.y`. Make some features from **Pyhton 3** will be backported to **Python 2**.

## Porting Python 2 to Pyhton 3 ##

**TODO**

Remove tasks once finished.

 * Create a function in `disk_IO.py` to write text files, arguments filename and slist. Use this function to write al reports and text files. Use `io.open`.

 * Call function in `utils_kodi` to display text window.

**Language specific issues**

 * The `urlparse` module is renamed to `urllib.parse` in Python 3.

 * The `StringIO` modules is gone. Use `io.StringIO` and `io.BytesIO`.

 * Python 2 unicode object is str object in Python 3. Python 2 str object is bytes in Python 3.

 * Python 2 dict.iteritems() must be converted to dict.items() 

   [StackOverflow: When should iteritems() be used instead of items()?](https://stackoverflow.com/questions/13998492/when-should-iteritems-be-used-instead-of-items)

 * Python 2 iterator method .next() is built-in function next(iterator) or .__next__() method in Python 3.

 * `xml.etree.cElementTree` is deprecated. It will be used automatically by `xml.etree.ElementTree` whenever available.

 * Use `io.open()` and not built-in `open()` in Python 2. `io.open()` in Python 2 supports the `encoding` argument and it's compatible with Python 3 `io.open()`. Moreover, in Python 3 `open()` is an alias of `io.open()`.

**Kodi specific issues**

 * AML Python 2 is Krypton compatible. This means in Python 3 all the API updates can be applied.

 * Kodi functions now take/return Unicode strings (str type in Python 3)

   [Kodi six](https://github.com/romanvm/kodi.six)

 * Leia change: Addon setting functions getSettingBool(), getSettingInt(), etc.

 * Matrix change: Addon settings *should* be converted. The old settings are deprecated, quoting from the wiki: "Deprecated - Addons submitted to the Kodi 19 Matrix (and up) can use the new setting format. See Add-on_settings_conversion."

   [Kodi wiki: Add-on settings](https://kodi.wiki/view/Add-on_settings) [Kodi wiki: Addon settings conversion](https://kodi.wiki/view/Add-on_settings_conversion) [Kodi Matrix alpha 1, addon settings do not show](https://forum.kodi.tv/showthread.php?tid=356245)

 * Matrix change: `XBMC.RunPlugin({}?command={})` must be changed to `XBMC.RunPlugin({}?command={})`.

 * Matrix change: `xbmcgui.Dialog().yesno()` add support for custom button.

 * Matrix change: `xbmcgui.Dialog().yesno()`, `.cancel()`, `.ok()`, `xbmcgui.DialogProgress().create()`, `.update()`, Removed Line2, Line3.

   All progress dialogs (search for `pDialog.create()` in the code) must use the new `KodiProgressDialog()` class.

**Travis errors**

Travis suggest using `list(dic.items())` instead of `dic.items()` when iterating the keys and values of a dictionary in Python 3. However, this can be harmful for performance!

```
-    for m_name, r_name in catalog_dic.items():
+    for m_name, r_name in list(catalog_dic.items()):
         sl.append('<machine>')
```

[Stack overflow: Difference between iterate dictionary.items() vs list(dictionary.items())](https://stackoverflow.com/questions/63706787/difference-between-iterate-dictionary-items-vs-listdictionary-items)

**References**

[The Conservative Python 3 Porting Guide](https://portingguide.readthedocs.io/en/latest/index.html)

[Kodi forum: Changes to the python API for Kodi Matrix](https://forum.kodi.tv/showthread.php?tid=344263)

[Kodi forum: Changes to the python API for Kodi Leia](https://forum.kodi.tv/showthread.php?tid=303073)

[Processing Text Files in Python 3](http://python-notes.curiousefficiency.org/en/latest/python3/text_file_processing.html)

## Installing multiple Kodi versions in Windows for development ##

 1. Download and then run the executable installer file for the version of Kodi you want to install. **You must change the installation location from the default location.**

 2. Find the `Kodi.exe` application in the folder you just installed. Right-click the application, and choose ‘Create shortcut’.

 3. Right-click the shortcut you created, and choose ‘Properties’. In the ‘Target’ text field, add the argument `-p` after the file location. 

 4. If you create another shortcut and fail to add the `-p` switch, or start this portable version of Kodi in a different way, then the default userdata folder will be created, and might overwrite your standard installation of Kodi, if you have one.

 5. The Kodi folder which you nominated above will be used to host the data folder (where Kodi stores scripts, plugins, skins and userdata) in a subfolder named `portable_data`. `portable_data` is mapped to `special://home/`.

**References**

[Kodi Wiki: HOW-TO:Install_Kodi_for_Windows](https://kodi.wiki/view/HOW-TO:Install_Kodi_for_Windows#Portable_Mode)

## Installing multiple Kodi versions in Linux for development ##

WRITE ME.

**References**

[Kodi forum: Development with several Kodi versions and userdata directories](https://forum.kodi.tv/showthread.php?tid=356152)

## Publishing AML into the Kodi repository (Tortoise Git) ##

**Setup**

First make sure the remote repository is OK. In `Tortoise Git`, `Settings`, in the `Remote` option there should be a remote named `upstream` with URL `https://github.com/xbmc/repo-plugins.git`.

**Updating repository**

Suppose we want to update the branch `krypton`. Use `Git show log` to make sure the repository is on the `krypton` branch.

To update the working copy with the contents of upstream use `Pull` with remote `upstream` and remote branch `krypton`.

**Update addon**

Create a branch with `Create branch...`. The branch name must be `plugin.program.AML`. Make the description the same as the branch name. Use the `Switch/Checkout...` command to switch to the new branch.

Make sure the repository is on the branch `plugin.program.AML`. Make the changes to update the addon and then do a single commit named `[plugin.program.AML] x.y.z`.

Push the branch `plugin.program.AML` to the remote `origin`. Finally, open the pull request in Github.

**Updating the pull request**

Updating your pull request can be done by applying your changes and squashing them in the already present commit.

**References**

[Kodi xbmc-repoplugins: CONTRIBUTING](https://github.com/xbmc/repo-plugins/blob/master/CONTRIBUTING.md)

## Kodi repository Travis rules ##

 * Screenshots maximum file size is 750 KB.

## Resolution table ##

| Name           | Resolution    | Notes                                                      |
|----------------|---------------|------------------------------------------------------------|
| SDTV 480i NTSC | ` 704 x  480` | AR 4:3 NTSC, 720 x 480 full frame with horizontal blanking |
| SDTV 576i PAL  | ` 704 x  576` | AR 4:3 NTSC, 720 x 576 full frame with horizontal blanking |
| Standard HD    | `1280 x  720` | AR 16:9                                                    |
| Full HD        | `1920 x 1080` | AR 16:9, informally referred as 2K                         |
| 4K Ultra HD    | `3840 x 2160` | AR 16:9                                                    |
| 8K Ultra HD    | `7680 x 4320` | AR 16:9                                                    |

 * In **SDTV** the pixel aspect ratio (PAR) is not square, and the PAR changes depending on the display aspect ratio (DAR). In other words, the SDTV resolution for 4:3 DAR or 16:9 DAR is the same, what changes is the pixel aspect ratio and hence the physical size of the display.

## MAME implicit/explicit ROM merging ##

ClrMAME Pro merges clone ROMs implicitly if a ROM with same CRC exists in the parent set. There is some info in PD forum about this.

## Known media types in MAME ###

Machines may have more than one media type. In this case, a number is appended at the end. For
example, a machine with 2 cartriged slots has `cartridge1` and `cartridge2`.

| Name       | Short name | Machine example  |
|------------|------------|------------------|
| cartridge  | cart       | 32x, sms, smspal |
| cassete    | cass       |                  |
| floppydisk | flop       |                  |
| quickload  | quick      |                  |
| snapshot   | dump       |                  |
| harddisk   | hard       |                  |
| cdrom      | cdrm       |                  |
| printer    | prin       |                  |

## Cartridges ###

Most consoles have only one cartridge slot, for example `32x`.

```
<machine name="32x" sourcefile="megadriv.cpp">
...
<device type="cartridge" tag="cartslot" mandatory="1" interface="_32x_cart">
    <instance name="cartridge" briefname="cart"/>
    <extension name="32x"/>
    <extension name="bin"/>
</device>
```

Device name and its brief version can be used at command line to launch a specific program/game.

```
mame 32x -cartridge foo1.32x
mame 32x -cart foo1.32x
```

A machine may have more than one cartridge slot, for example `abc110`.

```
<machine name="abc110" sourcefile="bbc.cpp" cloneof="bbcbp" romof="bbcbp">
...
<device type="cartridge" tag="exp_rom1" interface="bbc_cart">
    <instance name="cartridge1" briefname="cart1"/>
    <extension name="bin"/>
    <extension name="rom"/>
</device>
<device type="cartridge" tag="exp_rom2" interface="bbc_cart">
    <instance name="cartridge2" briefname="cart2"/>
    <extension name="bin"/>
    <extension name="rom"/>
</device>
...
```

Launching command example.

```
mame abc110 -cart1 foo1.bin -cart2 foo2.bin
```

## Launching Software Lists ##

Example of machines with SL: `32x`.

```
<machine name="32x" sourcefile="megadriv.cpp">
...
    <device type="cartridge" tag="cartslot" mandatory="1" interface="_32x_cart">
        <instance name="cartridge" briefname="cart"/>
        <extension name="32x"/>
        <extension name="bin"/>
    </device>
    <slot name="cartslot">
    </slot>
    <softwarelist name="32x" status="original" filter="NTSC-U" />
</machine>
```

**References**

[MESS wiki: HOWTO](http://mess.redump.net/mess/howto)

[MESS wiki: Software List Format](http://mess.redump.net/mess/swlist_format)

## Special SL items in Software Lists ##

### Implicit ROM merging ###

Software List XMLs do not have the ROM `merge` attribute. However, ClrMAME Pro merges SL
clone ROMs implicitly if a ROM with same CRC exists in the parent set.

SL `sms`, item `teddyboy` and `teddyboyc`.

### SL ROMS with `loadflag` attribute ###

MAME 0.196, SL `neogeo`, item `aof` "Art of Fighting / Ryuuko no Ken (NGM-044 ~ NGH-044)".

```
<software name="aof">
    <description>Art of Fighting / Ryuuko no Ken (NGM-044 ~ NGH-044)</description>
    <year>1992</year>
    <publisher>SNK</publisher>
    <info name="serial" value="NGM-044 (MVS), NGH-044 (AES)"/>
    <info name="release" value="19920924 (MVS), 19921211 (AES)"/>
    <info name="alt_title" value="龍虎の拳"/>
    <sharedfeat name="release" value="MVS,AES" />
    <sharedfeat name="compatibility" value="MVS,AES" />
    <part name="cart" interface="neo_cart">
        <dataarea name="maincpu" width="16" endianness="big" size="0x100000">
            <!-- TC534200 -->
            <rom loadflag="load16_word_swap" name="044-p1.p1" offset="0x000000" size="0x080000" crc="ca9f7a6d" sha1="4d28ef86696f7e832510a66d3e8eb6c93b5b91a1" />
        </dataarea>
        <dataarea name="fixed" size="0x040000">
            <!-- TC531000 -->
            <rom offset="0x000000" size="0x020000" name="044-s1.s1" crc="89903f39" sha1="a04a0c244a5d5c7a595fcf649107969635a6a8b6" />
        </dataarea>
        <dataarea name="audiocpu" size="0x020000">
            <!-- TC531001 -->
            <rom offset="0x000000" size="0x020000" name="044-m1.m1" crc="0987e4bb" sha1="8fae4b7fac09d46d4727928e609ed9d3711dbded" />
        </dataarea>
        <dataarea name="ymsnd" size="0x400000">
            <!-- TC5316200 -->
            <rom name="044-v2.v2" offset="0x000000" size="0x200000" crc="3ec632ea" sha1="e3f413f580b57f70d2dae16dbdacb797884d3fce" />
            <!-- TC5316200 -->
            <rom name="044-v4.v4" offset="0x200000" size="0x200000" crc="4b0f8e23" sha1="105da0cc5ba19869c7147fba8b177500758c232b" />
        </dataarea>
        <dataarea name="sprites" size="0x800000">
            <!-- TC5316200 -->
            <rom loadflag="load16_byte" name="044-c1.c1" offset="0x000000" size="0x100000" crc="ddab98a7" sha1="f20eb81ec431268798c142c482146c1545af1c24" />
            <rom size="0x100000" offset="0x400000" loadflag="continue" />
            <!-- TC5316200 -->
            <rom loadflag="load16_byte" name="044-c2.c2" offset="0x000001" size="0x100000" crc="d8ccd575" sha1="f697263fe92164e274bf34c55327b3d4a158b332" />
            <rom size="0x100000" offset="0x400001" loadflag="continue" />
            <!-- TC5316200 -->
            <rom loadflag="load16_byte" name="044-c3.c3" offset="0x200000" size="0x100000" crc="403e898a" sha1="dd5888f8b24a33b2c1f483316fe80c17849ccfc4" />
            <rom size="0x100000" offset="0x600000" loadflag="continue" />
            <!-- TC5316200 -->
            <rom loadflag="load16_byte" name="044-c4.c4" offset="0x200001" size="0x100000" crc="6235fbaa" sha1="9090e337d7beed25ba81ae0708d0aeb57e6cf405" />
            <rom size="0x100000" offset="0x600001" loadflag="continue" />
        </dataarea>
    </part>
</software>
```

## AML memory consumption in Windows ##

Windows 7 Ultimate version 6.1 64 bit, Kodi Krypton 17.6. MAME 0.197, Peak Working Set (Memory)
Kodi is restarted before each test.
Options: no ROM/Asset cache, with SLs.

Build all databases, no INIs/DATs                                              -> 863 MB
Build all databases, with INIs/DATs, with ROM/Asset cache, OPTION_COMPACT_JSON -> 866 MB
Build all databases, with INIs/DATs, with ROM/Asset cache                      -> 914 MB
Build all databases, with INIs/DATs                                            -> 916 MB
Build MAME database, with INIs/DATs                                            -> 916 MB
Build MAME Audit database, with INIs/DATs                                      -> 938 MB
Build MAME database, with INIs/DATs, OPTION_COMPACT_JSON                       -> 870 MB
Build MAME Audit database, with INIs/DATs, OPTION_COMPACT_JSON                 -> 905 MB

I coded an interative JSON writer. See [Stackoverflow: memoryerror-using-json-dumps](https://stackoverflow.com/questions/24239613/memoryerror-using-json-dumps). Options: no ROM/Asset cache, with SLs, with INIs/DATs.

Build all databases, older fast writer, OPTION_COMPACT_JSON -> Peak memory 867 MB
```
fs_write_JSON_file() "C:\Kodi\userdata\addon_data\plugin.program.AML\MAME_DB_main.json"
fs_write_JSON_file() Writing time 8.258000 s
fs_write_JSON_file() "C:\Kodi\userdata\addon_data\plugin.program.AML\MAME_DB_render.json"
fs_write_JSON_file() Writing time 2.981000 s
fs_write_JSON_file() "C:\Kodi\userdata\addon_data\plugin.program.AML\MAME_DB_roms.json"
fs_write_JSON_file() Writing time 13.724000 s
fs_write_JSON_file() "C:\Kodi\userdata\addon_data\plugin.program.AML\ROM_Audit_DB.json"
fs_write_JSON_file() Writing time 12.347000 s
```

Build all databases, newer slow writer, OPTION_COMPACT_JSON -> Peak memory 621 MB
```
fs_write_JSON_file_lowmem() "C:\Kodi\userdata\addon_data\plugin.program.AML\MAME_DB_main.json"
fs_write_JSON_file_lowmem() Writing time 13.526000 s
fs_write_JSON_file_lowmem() "C:\Kodi\userdata\addon_data\plugin.program.AML\MAME_DB_render.json"
fs_write_JSON_file_lowmem() Writing time 4.979000 s
fs_write_JSON_file_lowmem() "C:\Kodi\userdata\addon_data\plugin.program.AML\MAME_DB_roms.json"
fs_write_JSON_file_lowmem() Writing time 22.240000 s
fs_write_JSON_file_lowmem() "C:\Kodi\userdata\addon_data\plugin.program.AML\ROM_Audit_DB.json"
fs_write_JSON_file_lowmem() Writing time 20.663000 s
```

The iterative JSON encoder consumes much less memory and is about twice as slow.
