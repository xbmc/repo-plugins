[![GitHub release](https://img.shields.io/github/release/im85288/service.upnext.svg)](https://github.com/im85288/service.upnext/releases)
[![CI](https://github.com/im85288/service.upnext/workflows/CI/badge.svg)](https://github.com/im85288/service.upnext/actions?query=workflow:CI)
[![Codecov status](https://img.shields.io/codecov/c/github/im85288/service.upnext/master)](https://codecov.io/gh/im85288/service.upnext/branch/master)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv2-yellow.svg)](https://opensource.org/licenses/GPL-2.0)
[![Contributors](https://img.shields.io/github/contributors/im85288/service.upnext.svg)](https://github.com/im85288/service.upnext/graphs/contributors)

# Up Next - Proposes to play the next episode automatically

This Kodi add-on shows a Netflix-style notification for watching the next episode. After a few automatic iterations it asks the user if he is still there watching.

A lot of existing add-ons already integrate with this service out-of-the-box.

## Settings
The add-on has various settings to fine-tune the experience, however the default settings should be fine for most.

  * Simple or fancy mode (defaults to fancy mode, but a more simple interface is possible)
  * The notification time can be adjusted (defaults to 30 seconds before the end)
  * The default action can be confnigured, i.e. should it advance to the next episode (default) when the user does not respond, or stop
  * The number of episodes to play automatically before asking the user if he is still there (defaults to 3 episodes)

> NOTE: The add-on settings are found in the Kodi add-ons section, in the *Services* category.

For [Addon Integration](https://github.com/im85288/service.upnext/wiki/Addon-Integration) and [Skinners](https://github.com/im85288/service.upnext/wiki/Skinners) see the [wiki](https://github.com/im85288/service.upnext/wiki)

## Releases
### v1.1.1 (2020-06-21)
- Avoid conflict with external players (@BrutuZ)
- Restore "Ignore Playlist" option (@BrutuZ)
- Fix a known Kodi bug related to displaying hours (@Maven85)
- Improvements to endtime visualization (@dagwieers)
- New translations for Hindi and Romanian (@tahirdon, @tmihai20)
- Translation updates to Hungarian and Spanish (@frodo19, @roliverosc)

### v1.1.0 (2020-01-17)
- Add notification_offset for Netflix add-on (@CastagnaIT)
- Fix various runtime exceptions (@thebertster)
- Implement new settings (@dagwieers)
- Implement new developer mode (@dagwieers)
- Show current time and next endtime in notification (@dagwieers)
- New translations for Brazilian, Czech, Greek, Japanese, Korean (@mediabrasiltv, @svetlemodry, @Twilight0, @Thunderbird2086)
- New translations for Russian, Slovak, Spanish, Swedish (@vlmaksime, @matejmosko, @sagatxxx, @Sopor)
- Translation updates to Croatian, French, German, Hungarian, Italian, Polish (@arvvoid, @zecakeh, @tweimer, @frodo19, @EffeF, @notoco)
