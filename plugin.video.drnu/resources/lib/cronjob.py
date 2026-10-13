#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Removal of the deprecated service.cronxbmc job.

The re-cache schedule is handled by the addon's own background service
since 7.1.0; this module only deletes any job an older version registered
in cronxbmc, so upgrades don't leave a 03:00 GUI-poking job behind. The
cronxbmc dependency is gone from addon.xml, so the import is lazy and the
removal is silently skipped when cronxbmc is not installed.
"""

JOB_NAME = "plugin.video.drnu cronjob"


def remove_cronjob() -> None:
    """Delete the drnu job in cronxbmc, if cronxbmc is installed and has one."""
    try:
        from cron import CronManager
    except ImportError:
        return
    manager = CronManager()
    for job in manager.getJobs():
        if job.name == JOB_NAME:
            manager.deleteJob(job.id)
            break
