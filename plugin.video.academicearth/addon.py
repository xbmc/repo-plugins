#!/usr/bin/env python
# Copyright 2011 Jonathan Beluch.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from operator import itemgetter
from xbmcswift2 import Plugin
from resources.lib.academicearth import api

PLUGIN_NAME = 'Academic Earth'
PLUGIN_ID = 'plugin.video.academicearth'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)


@plugin.route('/')
def show_index():
    items = [
        {'label': plugin.get_string(30200),
         'path': plugin.url_for('show_subjects')},

        {'label': plugin.get_string(30201),
         'path': plugin.url_for('show_universities')},

        {'label': plugin.get_string(30202),
         'path': plugin.url_for('show_speakers')},
    ]
    return items


@plugin.route('/universities/')
def show_universities():
    ae = api.AcademicEarth()
    unis = ae.get_universities()

    items = [{
        'label': uni.name,
        'path': plugin.url_for('show_university_info', url=uni.url),
        'icon': uni.icon,
    } for uni in unis]

    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items


@plugin.route('/subjects/')
def show_subjects():
    ae = api.AcademicEarth()
    subjects = ae.get_subjects()

    items = [{
        'label': subject.name,
        'path': plugin.url_for('show_subject_info', url=subject.url),
    } for subject in subjects]

    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items


@plugin.route('/speakers/')
def show_speakers():
    ae = api.AcademicEarth()
    speakers = ae.get_speakers()

    items = [{
        'label': speaker.name,
        'path': plugin.url_for('show_speaker_info', url=speaker.url),
    } for speaker in speakers]

    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items


@plugin.route('/subjects/<url>/', 'show_subject_info', {'cls': api.Subject})
@plugin.route('/universities/<url>/', 'show_university_info',
              {'cls': api.University})
@plugin.route('/speakers/<url>/', 'show_speaker_info', {'cls': api.Speaker})
def show_info(url, cls):
    uni = cls.from_url(url)

    courses = [{
        'label': course.name,
        'path': plugin.url_for('show_course_info', url=course.url),
    } for course in uni.courses]

    lectures = [{
        'label': 'Lecture: %s' % lecture.name,
        'path': plugin.url_for('play_lecture', url=lecture.url),
        'is_playable': True,
    } for lecture in uni.lectures]

    by_label = itemgetter('label')
    items = sorted(courses, key=by_label) + sorted(lectures, key=by_label)
    return items


@plugin.route('/courses/<url>/')
def show_course_info(url):
    course = api.Course.from_url(url)
    lectures = [{
        'label': 'Lecture: %s' % lecture.name,
        'path': plugin.url_for('play_lecture', url=lecture.url),
        'is_playable': True,
    } for lecture in course.lectures]

    return sorted(lectures, key=itemgetter('label'))


@plugin.route('/lectures/<url>/')
def play_lecture(url):
    lecture = api.Lecture.from_url(url)
    ptn = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
    url = ptn % lecture.youtube_id
    plugin.log.info('Playing url: %s' % url)
    plugin.set_resolved_url(url)


if __name__ == '__main__':
    plugin.run()
