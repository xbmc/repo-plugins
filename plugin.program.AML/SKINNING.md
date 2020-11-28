# Advanced MAME Launcher metadata and artwork model #

AML metadata/assets model is as much compatible with [Advanced Emulator Launcher] as possible.

[Advanced Emulator Launcher]: http://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/

## MAME machine metadata labels ##

| Metadata name | setInfo label | setProperty label | Infolabel                            |
|---------------|---------------|-------------------|--------------------------------------|
| Title         | title         |                   | `$INFO[ListItem.Label]`              |
| Year          | year          |                   | `$INFO[ListItem.Year]`               |
| Genre         | genre         |                   | `$INFO[ListItem.Genre]`              |
| Manufacturer  | studio        |                   | `$INFO[ListItem.Studio]`             |
| Plot          | plot          |                   | `$INFO[ListItem.Plot]`               |
| NPlayers      |               | nplayers          | `$INFO[ListItem.Property(nplayers)]` |
| Platform      |               | platform          | `$INFO[ListItem.Property(platform)]` |
| History.DAT   |               | history           | `$INFO[ListItem.Property(history)]`  |

## MAME machine asset labels ##

| Asset name | setArt label | setInfo label | Infolabel                        |
|------------|--------------|---------------|----------------------------------|
| Title      | title        |               | `$INFO[ListItem.Art(title)]`     |
| Snap       | snap         |               | `$INFO[ListItem.Art(snap)]`      |
| Cabinet    | boxfront     |               | `$INFO[ListItem.Art(boxfront)]`  |
| CPanel     | boxback      |               | `$INFO[ListItem.Art(boxback)]`   |
| PCB        | cartridge    |               | `$INFO[ListItem.Art(cartridge)]` |
| Flyer      | flyer        |               | `$INFO[ListItem.Art(flyer)]`     |
| 3D Box     | 3dbox        |               | `$INFO[ListItem.Art(3dbox)]`     |
| Icon       | icon         |               | `$INFO[ListItem.Icon]`           |
| Fanart     | fanart       |               | `$INFO[ListItem.Fanart]`         |
| Marquee    | banner       |               | `$INFO[ListItem.Art(banner)]`    |
| Clearlogo  | clearlogo    |               | `$INFO[ListItem.Art(clearlogo)]` |
| Flyer      | poster       |               | `$INFO[ListItem.Art(poster)]`    |
| Trailer    |              | trailer       | `$INFO[ListItem.trailer]`        |

## MAME machine asset availability ##

| Artwork site      | Title | Snap  | Preview | Boss | End | GameOver | HowTo | Logo | Scores | Select |
|-------------------|-------|-------|---------|------|-----|----------|-------|------|--------|--------|
| [Pleasuredome]    |  YES  | YES   | YES     | YES  | YES |    YES   |  YES  | YES  |  YES   |  YES   |
| [ProgrrettoSNAPS] |  YES  | YES   | YES     | YES  | YES |    YES   |  YES  | YES  |  YES   |  YES   |


| Artwork site      | Versus | Cabinet | CPanel | Flyer  | Icon | Marquee | PCB | Manual | Trailer |
|-------------------|--------|---------|--------|--------|------|---------|-----|--------|---------|
| [Pleasuredome]    |  YES   |  YES    |  YES   |  YES   | YES  |   YES   | YES |  YES   |  YES    |
| [ProgrrettoSNAPS] |  YES   |  YES    |  YES   |  YES   | YES  |   YES   | YES |  YES   |  YES    |


## Software Lists asset availability ##

| Artwork site      |  Title | Snap | Fanart | Banner | Boxfront | Boxback  | Manual | Trailer | 
|-------------------|--------|------|--------|--------|----------|----------|--------|---------|
| [Pleasuredome]    |  YES   | YES  | NO     | NO     |   YES    |   NO     |  YES   | YES     |
| [ProgrrettoSNAPS] |  YES   | YES  | NO     | NO     |   YES    |   NO     |  YES   | YES     |

 * Many consoles/computers have the same artwork as arcade. For MAME, both arcade and
   consoles/computers are just "machines". For example, CPanel of MegaDrive is the 
   SEGA 3 button joystick.

[Pleasuredome]: http://www.pleasuredome.org.uk/
[ProgrrettoSNAPS]: http://www.progettosnaps.net
