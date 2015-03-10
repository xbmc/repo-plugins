from resources.lib.kodion.items import VideoItem, NextPageItem
from resources.lib.kodion.items.directory_item import DirectoryItem

__author__ = 'bromix'

import xml.etree.ElementTree as ET


def do_xml_to_video_stream(context, provider, xml):
    def _sort(x):
        return x['resolution']

    result = []
    root = ET.fromstring(xml)
    video = root.find('video')
    if video is not None:
        for video_file in video.iter('file'):
            height = int(video_file.get('height'))
            url = video_file.get('url')
            mime_type = video_file.get('mime_type')

            video_info = {'url': url,
                          'resolution': height,
                          'format': mime_type}
            result.append(video_info)
            pass
        pass

    result = sorted(result, key=_sort, reverse=False)
    return result


def _do_next_page(result, xml_element, context, provider):
    if len(result) > 0:
        current_page = int(xml_element.get('page', '1'))
        items_per_page = int(xml_element.get('perpage', '1'))
        total_items = int(xml_element.get('total', '1'))
        if items_per_page * current_page < total_items:
            next_page_item = NextPageItem(context, current_page)
            next_page_item.set_fanart(provider.get_fanart(context))
            result.append(next_page_item)
            pass
        pass
    pass
    pass


def do_xml_error(context, provider, root_element):
    if isinstance(root_element, basestring):
        root_element = ET.fromstring(root_element)
        pass

    status = root_element.get('stat')
    if status == 'fail':
        error_item = root_element.find('err')
        if error_item is not None:
            message = error_item.get('msg')
            explanation = error_item.get('expl')
            message = '%s - %s' % (message, explanation)
            context.get_ui().show_notification(message, time_milliseconds=15000)
            pass
        pass
    pass


def do_xml_video_response(context, provider, video_xml):
    if isinstance(video_xml, basestring):
        video_xml = ET.fromstring(video_xml)
        do_xml_error(context, provider, video_xml)
        video_xml = video_xml.find('video')
        pass

    video_id = video_xml.get('id')
    title = video_xml.find('title').text
    video_item = VideoItem(title, context.create_uri(['play'], {'video_id': video_id}))

    # channel name
    channel_name = ''
    owner = video_xml.find('owner')
    if owner is not None:
        channel_name = owner.get('username', '')
        pass
    video_item.set_studio(channel_name)
    video_item.add_artist(channel_name)

    # date
    upload_date = video_xml.find('upload_date')
    if upload_date is not None and upload_date.text is not None:
        upload_date = upload_date.text
        upload_date = upload_date.split(' ')
        if len(upload_date) == 2:
            date = upload_date[0].split('-')
            time = upload_date[1].split(':')
            if len(date) == 3 and len(time) == 3:
                video_item.set_date(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]),
                                    int(time[2]))
                video_item.set_year(int(date[0]))
                video_item.set_aired(int(date[0]), int(date[1]), int(date[2]))
                video_item.set_premiered(int(date[0]), int(date[1]), int(date[2]))
                pass
            pass
        pass

    # plot
    plot = video_xml.find('description').text
    if plot is None:
        plot = ''
        pass

    settings = context.get_settings()
    if channel_name and settings.get_bool('vimeo.view.description.show_channel_name', True):
        plot = '[UPPERCASE][B]%s[/B][/UPPERCASE][CR][CR]%s' % (channel_name, plot)
        pass
    video_item.set_plot(plot)

    # duration
    duration = int(video_xml.find('duration', '0').text)
    if duration is not None:
        video_item.set_duration_from_seconds(duration)
        pass

    # thumbs
    thumbnails = video_xml.find('thumbnails')
    if thumbnails is not None:
        for thumbnail in video_xml.iter('thumbnail'):
            height = int(thumbnail.get('height', '0'))
            if height >= 360:
                video_item.set_image(thumbnail.text)
                break
            pass
        pass
    video_item.set_fanart(provider.get_fanart(context))

    # context menu
    context_menu = []
    if provider.is_logged_in():
        # like/unlike
        is_like = video_xml.get('is_like', '0') == '1'
        if is_like:
            like_text = context.localize(provider._local_map['vimeo.unlike'])
            context_menu.append(
                (like_text, 'RunPlugin(%s)' % context.create_uri(['video', 'unlike'], {'video_id': video_id})))
        else:
            like_text = context.localize(provider._local_map['vimeo.like'])
            context_menu.append(
                (like_text, 'RunPlugin(%s)' % context.create_uri(['video', 'like'], {'video_id': video_id})))
            pass

        # watch later
        is_watch_later = video_xml.get('is_watchlater', '0') == '1'
        if is_watch_later:
            watch_later_text = context.localize(provider._local_map['vimeo.watch-later.remove'])
            context_menu.append(
                (watch_later_text,
                 'RunPlugin(%s)' % context.create_uri(['video', video_id, 'watch-later'], {'later': '0'})))
        else:
            watch_later_text = context.localize(provider._local_map['vimeo.watch-later.add'])
            context_menu.append(
                (watch_later_text,
                 'RunPlugin(%s)' % context.create_uri(['video', video_id, 'watch-later'], {'later': '1'})))
            pass
        pass

    # Go to user
    owner = video_xml.find('owner')
    if owner is not None:
        owner_name = owner.get('display_name')
        owner_id = owner.get('id')
        context_menu.append((context.localize(provider._local_map['vimeo.user.go-to']) % '[B]'+owner_name+'[/B]',
                            'Container.Update(%s)' % context.create_uri(['user', owner_id])))
        pass

    video_item.set_context_menu(context_menu)
    return video_item


def do_xml_videos_response(context, provider, xml):
    result = []
    root = ET.fromstring(xml)
    do_xml_error(context, provider, root)

    videos = root.find('videos')
    if videos is not None:
        for video in videos.iter('video'):
            result.append(do_xml_video_response(context, provider, video))
            pass

        _do_next_page(result, videos, context, provider)
    return result


def do_xml_channel_response(context, provider, channel):
    if isinstance(channel, basestring):
        channel = ET.fromstring(channel)
        do_xml_error(context, provider, channel)
        channel = channel.find('video')
        pass

    channel_id = channel.get('id')
    channel_name = channel.find('name').text
    is_subscribed = channel.get('is_subscribed', '0') == '1'
    if provider.is_logged_in() and not is_subscribed:
        channel_name = '[I]%s[/I]' % channel_name
        pass

    image = ''
    logo_url = channel.find('logo_url')
    if logo_url is not None and logo_url.text:
        image = logo_url.text
    else:
        thumbnail_url = channel.find('thumbnail_url')
        if thumbnail_url is not None:
            image = thumbnail_url.text.replace('200x150', '400x300')
            pass
        pass

    channel_item = DirectoryItem(channel_name, context.create_uri(['channel', channel_id]), image=image)

    # context menu
    context_menu = []
    if provider.is_logged_in():
        # join/leave
        if is_subscribed:
            text = context.localize(provider._local_map['vimeo.channel.unfollow'])
            context_menu.append(
                (text, 'RunPlugin(%s)' % context.create_uri(['channel', 'unsubscribe'], {'channel_id': channel_id})))
        else:
            text = context.localize(provider._local_map['vimeo.channel.follow'])
            context_menu.append(
                (text, 'RunPlugin(%s)' % context.create_uri(['channel', 'subscribe'], {'channel_id': channel_id})))
            pass
        pass
    channel_item.set_context_menu(context_menu)

    return channel_item


def do_xml_channels_response(context, provider, xml):
    result = []
    root = ET.fromstring(xml)
    do_xml_error(context, provider, root)

    channels = root.find('channels')
    if channels is not None:
        for channel in channels.iter('channel'):
            result.append(do_xml_channel_response(context, provider, channel))
            pass

        _do_next_page(result, channels, context, provider)
    return result


def do_xml_album_response(user_id, context, provider, album):
    if isinstance(album, basestring):
        album = ET.fromstring(album)
        do_xml_error(context, provider, album)
        album = album.find('album')
        pass

    album_id = album.get('id')
    album_name = album.find('title').text

    album_item = DirectoryItem(album_name, context.create_uri(['user', user_id, 'album', album_id]))

    thumbnail_video = album.find('thumbnail_video')
    if thumbnail_video is not None:
        thumbnails = thumbnail_video.find('thumbnails')
        if thumbnails is not None:
            for thumbnail in thumbnails.iter('thumbnail'):
                height = int(thumbnail.get('height', '0'))
                if height >= 360:
                    album_item.set_image(thumbnail.text)
                    break
                pass
            pass
        pass
    return album_item


def do_xml_albums_response(user_id, context, provider, xml):
    result = []
    root = ET.fromstring(xml)
    do_xml_error(context, provider, root)

    albums = root.find('albums')
    if albums is not None:
        for album in albums.iter('album'):
            result.append(do_xml_album_response(user_id, context, provider, album))
            pass

        _do_next_page(result, albums, context, provider)
    return result


def do_xml_group_response(context, provider, group):
    if isinstance(group, basestring):
        group = ET.fromstring(group)
        do_xml_error(context, provider, group)
        group = group.find('video')
        pass

    group_id = group.get('id')
    group_name = group.find('name').text
    has_joined = group.get('has_joined', '0') == '1'
    if provider.is_logged_in() and not has_joined:
        group_name = '[I]%s[/I]' % group_name
        pass

    logo_url = group.find('logo_url')
    image = ''
    if logo_url is not None and logo_url.text:
        image = logo_url.text
    else:
        thumbnail_url = group.find('thumbnail_url')
        if thumbnail_url is not None:
            image = thumbnail_url.text.replace('200x150', '400x300')
            pass
        pass

    group_item = DirectoryItem(group_name, context.create_uri(['group', group_id]), image=image)

    # context menu
    context_menu = []
    if provider.is_logged_in():
        # join/leave
        if has_joined:
            leave_text = context.localize(provider._local_map['vimeo.group.leave'])
            context_menu.append(
                (leave_text, 'RunPlugin(%s)' % context.create_uri(['group', 'leave'], {'group_id': group_id})))
        else:
            join_text = context.localize(provider._local_map['vimeo.group.join'])
            context_menu.append(
                (join_text, 'RunPlugin(%s)' % context.create_uri(['group', 'join'], {'group_id': group_id})))
            pass
        pass
    group_item.set_context_menu(context_menu)

    return group_item


def do_xml_groups_response(context, provider, xml):
    result = []
    root = ET.fromstring(xml)
    do_xml_error(context, provider, root)

    groups = root.find('groups')
    if groups is not None:
        for group in groups.iter('group'):
            result.append(do_xml_group_response(context, provider, group))
            pass

        _do_next_page(result, groups, context, provider)
    return result


def do_xml_user_response(context, provider, xml):
    result = []
    root = ET.fromstring(xml)
    do_xml_error(context, provider, root)

    contacts = root.find('contacts')
    if contacts is not None:
        for contact in contacts.iter('contact'):
            user_id = contact.get('id')
            username = contact.get('username')
            display_name = contact.get('display_name')

            contact_item = DirectoryItem(display_name, context.create_uri(['user', user_id]))

            # portraits
            portraits = contact.find('portraits')
            if portraits is not None:
                for portrait in portraits.iter('portrait'):
                    height = int(portrait.get('height', '0'))
                    if height >= 256:
                        contact_item.set_image(portrait.text)
                        break
                    pass
                pass

            contact_item.set_fanart(provider.get_fanart(context))
            result.append(contact_item)
            pass

        # add next page
        _do_next_page(result, contacts, context, provider)
        pass

    return result