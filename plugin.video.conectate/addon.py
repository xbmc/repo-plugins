#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Andres Trapanotto (andres.trapanotto@gmail.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Features
# * Conectate.gob.ar support for sub-sites: Encuentro, PakaPaka, Ronda, Conectar Igualdad
# * Section support for "Pelicula" , "Especial", "Serie", "Micro"
# * Page support 
# * HD/SD format selected by add-on setting (fallback to SD if HD not available)
# * Subtitles support
#
# ToDo:
#   To add Sort By
#   To add Search
#   To add Clud

from xbmcswift2 import Plugin
import resources.lib.videos_scraper as videos_scraper

STRINGS = {
    'page':                30001,
    'encuentro_pelicula':  30101,
    'encuentro_especial':  30102,
    'encuentro_serie':     30103,
    'encuentro_micros':    30104,
    'pakapaka_serie':      30203,
    'pakapaka_micros':     30204,
    'ronda_serie':         30303,
    'ronda_micros':        30304,
    'educar_especial':     30502,
    'ci_especial':         30602,

}

plugin = Plugin()


@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('encuentro_pelicula'),
         'thumbnail': 'http://www.encuentro.gob.ar/img/sitios/encuentro/encuentro_logo.gif',
         'path': plugin.url_for('shows_encuentro_pelicula',
            page='1',
            )},
        {'label': _('encuentro_especial'),
         'thumbnail': 'http://www.encuentro.gob.ar/img/sitios/encuentro/encuentro_logo.gif',
         'path': plugin.url_for('shows_encuentro_especial',
            page='1',
            )},
        {'label': _('encuentro_serie'),
         'thumbnail': 'http://www.encuentro.gob.ar/img/sitios/encuentro/encuentro_logo.gif',
         'path': plugin.url_for('shows_encuentro_serie',
            page='1',
            )},
        {'label': _('encuentro_micros'),
         'thumbnail': 'http://www.encuentro.gob.ar/img/sitios/encuentro/encuentro_logo.gif',
         'path': plugin.url_for('shows_encuentro_micros',
            page='1',
            )},
        {'label': _('pakapaka_serie'),
         'thumbnail': 'http://www.pakapaka.gob.ar/img/sitios/pakapaka/idSitio-pkpk.png',
         'path': plugin.url_for('shows_pakapaka_serie',
            page='1',
            )},
        {'label': _('pakapaka_micros'),
         'thumbnail': 'http://www.pakapaka.gob.ar/img/sitios/pakapaka/idSitio-pkpk.png',
         'path': plugin.url_for('shows_pakapaka_micros',
            page='1',
            )},
        {'label': _('ronda_serie'),
         'thumbnail': 'http://www.pakapaka.gob.ar/img/sitios/pakapaka/idSitio-pkpk.png',
         'path': plugin.url_for('shows_ronda_serie',
            page='1',
            )},
        {'label': _('ronda_micros'),
         'thumbnail': 'http://www.pakapaka.gob.ar/img/sitios/pakapaka/idSitio-pkpk.png',
         'path': plugin.url_for('shows_ronda_micros',
            page='1',
            )},
        {'label': _('educar_especial'),
         'thumbnail': 'http://www.educ.ar/img/sitios/educar/logo-educar.png',
         'path': plugin.url_for('shows_educar_especial',
            page='1',
            )},
        {'label': _('ci_especial'),
         'thumbnail': 'http://www.conectarigualdad.gob.ar/img/logo_conectar-igualdad.png',
         'path': plugin.url_for('shows_ci_especial',
            page='1',
            )}
    ]
    return plugin.finish(items)


@plugin.route('/encuentro_pelicula/<page>')
def shows_encuentro_pelicula(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=1&canalId=1&tipoEmisionId=1'
    videos = scraper.get_single_episodes(menuargc, page)
    count = len(videos)
    items = __format_videos(videos)

    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_pelicula',
                show_name='Pelicula',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_pelicula',
                show_name='Pelicula',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/encuentro_especial/<page>')
def shows_encuentro_especial(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=1&canalId=1&tipoEmisionId=2'
    videos = scraper.get_single_episodes(menuargc, page)
    count = len(videos)
    items = __format_videos(videos)

    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_especial',
                show_name='Especial',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_especial',
                show_name='Especial',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/encuentro_serie/<page>/')
def shows_encuentro_serie(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=1&canalId=1&tipoEmisionId=3'
    shows = scraper.get_show_names(menuargc, page)
    count = len(shows)
    items = __format_shows(shows)
    
    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_serie',
                show_name='Serie',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_serie',
                show_name='Serie',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/encuentro_micros/<page>')
def shows_encuentro_micros(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=1&canalId=1&tipoEmisionId=4'
    shows = scraper.get_show_names(menuargc, page)
    count = len(shows)
    items = __format_shows(shows)

    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_micros',
                show_name='Micros',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_encuentro_micros',
                show_name='Micros',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/pakapaka_serie/<page>/')
def shows_pakapaka_serie(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=2&canalId=2&tipoEmisionId=3'
    shows = scraper.get_show_names(menuargc, page)
    count = len(shows)
    items = __format_shows(shows)
    
    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_pakapaka_serie',
                show_name='Serie',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_pakapaka_serie',
                show_name='Serie',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/pakapaka_micros/<page>')
def shows_pakapaka_micros(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=2&canalId=2&tipoEmisionId=4'
    shows = scraper.get_show_names(menuargc, page)
    count = len(shows)
    items = __format_shows(shows)

    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_pakapaka_micros',
                show_name='Micros',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_pakapaka_micros',
                show_name='Micros',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/ronda_serie/<page>/')
def shows_ronda_serie(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=1&canalId=1&tipoEmisionId=3'
    shows = scraper.get_show_names(menuargc, page)
    count = len(shows)
    items = __format_shows(shows)
    
    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_ronda_serie',
                show_name='Serie',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_ronda_serie',
                show_name='Serie',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/ronda_micros/<page>')
def shows_ronda_micros(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=1&canalId=1&tipoEmisionId=4'
    shows = scraper.get_show_names(menuargc, page)
    count = len(shows)
    items = __format_shows(shows)

    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_ronda_micros',
                show_name='Micros',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_ronda_micros',
                show_name='Micros',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/educar_especial/<page>')
def shows_educar_especial(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=125&canalId=125&tipoEmisionId=2'
    videos = scraper.get_single_episodes(menuargc, page)
    count = len(videos)
    items = __format_videos(videos)

    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_educar_especial',
                show_name='Especial',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_educar_especial',
                show_name='Especial',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/ci_especial/<page>')
def shows_ci_especial(page):
    scraper = videos_scraper.Scraper()
    page = int(page)
    menuargc='temaCanalId=126&canalId=126&tipoEmisionId=2'
    videos = scraper.get_single_episodes(menuargc, page)
    count = len(videos)
    items = __format_videos(videos)

    if count >= 15:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='shows_ci_especial',
                show_name='Especial',
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='shows_ci_especial',
                show_name='Especial',
                page=previous_page,
                update='true')
        })

    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/videos/<show_name>/')
def show_episodes_by_show(show_name):
    scraper = videos_scraper.Scraper()
    videos  = scraper.get_episodes_by_show_name(show_name)
    items   = __format_videos(videos)
    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<id>')
def play_video(id):
    video = videos_scraper.Scraper().get_video(id)
    return plugin.set_resolved_url(item=video['url'], subtitles=video['url_sub'])

def __format_videos(videos):
    items = [{
        'label': video['title'],
        'thumbnail': video['thumbnail'],
        'info': {
            'count': i,
            'studio': video['duration'],
            'originaltitle': video['title'],
            'plot': video['description'],
            'date': video['date'],
            'size': video['filesize'],
            'credits': video['author'],
            'genre': ' | '.join(video['genres'])
        },
        'is_playable': True,
        'path': plugin.url_for(
            endpoint='play_video',
            id=video['id']
        ),
    } for i, video in enumerate(videos)]
    return items

def __format_shows(shows):
    items = [{
        'label': show['name'],
        'path': plugin.url_for(
            endpoint='show_episodes_by_show',
            show_name=show['id']
        ),
        'icon': show['icon'],
    } for show in shows]
    return items

def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id

def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    plugin.run()
