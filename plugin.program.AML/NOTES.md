## Launching MAME machines with media types (former MESS) ##

http://www.mess.org/mess/howto

### Known media types in MAME ###

 Name      | Short name | Machine example  |
-----------|------------|------------------|
cartridge  | cart       | 32x, sms, smspal |
cassete    | cass       |                  |
floppydisk | flop       |                  |
quickload  | quick      |                  |
snapshot   | dump       |                  |
harddisk   | hard       |                  |
cdrom      | cdrm       |                  |
printer    | prin       |                  |

Machines may have more than one media type. In this case, a number is appended at the end. For
example, a machine with 2 cartriged slots has `cartridge1` and `cartridge2`.

### Cartridges ###

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

http://www.mess.org/mess/howto#software_lists

http://www.mess.org/mess/swlist_format

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

## Memory consumption ##

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

I coded an interative JSON writer. See https://stackoverflow.com/questions/24239613/memoryerror-using-json-dumps
Options: no ROM/Asset cache, with SLs, with INIs/DATs.

Build all databases, older fast writer, OPTION_COMPACT_JSON -> 867 MB
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

Build all databases, newer slow writer, OPTION_COMPACT_JSON -> 621 MB
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

## Publishing AML into the Kodi repository (Tortoise Git) ##

[CONTRIBUTING](https://github.com/xbmc/repo-plugins/blob/master/CONTRIBUTING.md)

**Setup**

First make sure the remote repository is OK. In `Tortoise Git`, `Settings`, in the `Remote`
option there should be a remote named `upstream` with 
URL `https://github.com/xbmc/repo-plugins.git`.

**Updating repository**

Suppose we want to update the branch `krypton`. Use `Git show log` to make sure the
repository is on the `krypton` branch.

To update the working copy with the contents of upstream use `Pull` with remote `upstream` and
remote branch `krypton`.

**Update addon**

Create a branch with `Create branch...`. The branch name must be `plugin.program.AML`.
Make the description the same as the branch name. Use the `Switch/Checkout...` command to
switch to the new branch.

Make sure the repository is on the branch `plugin.program.AML`. Make the changes to update
the addon and then do a single commit named `[plugin.program.AML] x.y.z`.

Push the branch `plugin.program.AML` to the remote `origin`. Finally, open the pull request
in Github.

**Updating the pull request**

Updating your pull request can be done by applying your changes and squashing them
in the already present commit.
