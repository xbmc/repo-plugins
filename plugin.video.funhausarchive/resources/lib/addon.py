# -*- coding: utf-8 -*-
"""Funhaus Archive - Kodi Video Plugin Controller.

Browse and stream Funhaus videos from funhausarchive.com.
"""

import math
import sys
import urllib.parse
from typing import List, Dict, Any, Optional

try:
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcplugin

    KODI_AVAILABLE = True
except ImportError:
    KODI_AVAILABLE = False

from resources.lib.cache import SimpleCache
from resources.lib.navigation import NavigationManager
from resources.lib.resolver import VideoResolver
from resources.lib.scraper import FunhausScraper

ADDON_ID = "plugin.video.funhausarchive"


class FunhausAddon:
    """Main routing and view controller for Funhaus Archive Kodi Add-on."""

    def __init__(self, base_url: str, handle_str: str, query_str: str):
        self.base_url = base_url
        self.handle = int(handle_str) if handle_str and handle_str.lstrip('-').isdigit() else -1
        self.params = dict(urllib.parse.parse_qsl(query_str.lstrip('?')))

        if KODI_AVAILABLE:
            self.addon = xbmcaddon.Addon(ADDON_ID)
            self.addon_icon = self.addon.getAddonInfo('icon')
            self.addon_fanart = self.addon.getAddonInfo('fanart')
            cache_enabled = self.addon.getSettingBool('cache_enabled') if hasattr(self.addon, 'getSettingBool') else True
            cache_ttl = self.addon.getSettingInt('cache_ttl_hours') if hasattr(self.addon, 'getSettingInt') else 24
            video_quality = self.addon.getSetting('video_quality') or '1080p'
            playback_pref = self.addon.getSetting('playback_method') or 'YouTube Add-on'
            playback_method = "youtube_addon" if "YouTube" in playback_pref else "yt_dlp"
            page_size_setting = self.addon.getSetting('page_size') or '100'
            self.page_size = int(page_size_setting) if page_size_setting.isdigit() else 0
            self.remember_last_page = self.addon.getSettingBool('remember_last_page') if hasattr(self.addon, 'getSettingBool') else True
        else:
            self.addon = None
            self.addon_icon = ""
            self.addon_fanart = ""
            cache_enabled = True
            cache_ttl = 24
            video_quality = '1080p'
            playback_method = 'youtube_addon'
            self.page_size = 100
            self.remember_last_page = True

        self.cache = SimpleCache(default_ttl_hours=cache_ttl) if cache_enabled else None
        self.nav_mgr = NavigationManager()
        self.scraper = FunhausScraper(cache=self.cache)
        self.resolver = VideoResolver(playback_method=playback_method, preferred_quality=video_quality)

    def _get_string(self, string_id: int, default: str = "") -> str:
        """Retrieves localized string from strings.po if running inside Kodi."""
        if self.addon:
            try:
                localized = self.addon.getLocalizedString(string_id)
                if localized:
                    return localized
            except Exception:
                pass
        return default

    def _set_video_info(self, item: Any, title: str, tvshowtitle: str = "", plot: str = "",
                        duration: int = 0, upload_date: str = "", mediatype: str = "video"):
        """Sets video metadata using InfoTagVideo on Kodi 20+ with fallback to setInfo."""
        if hasattr(item, 'getVideoInfoTag'):
            try:
                tag = item.getVideoInfoTag()
                if title:
                    tag.setTitle(title)
                if tvshowtitle:
                    tag.setTvShowTitle(tvshowtitle)
                if plot:
                    tag.setPlot(plot)
                if duration:
                    tag.setDuration(duration)
                if upload_date:
                    tag.setPremiered(upload_date)
                    tag.setFirstAired(upload_date)
                if mediatype:
                    tag.setMediaType(mediatype)
                return
            except Exception:
                pass

        info_dict = {
            'title': title,
            'tvshowtitle': tvshowtitle,
            'plot': plot,
            'duration': duration,
            'mediatype': mediatype
        }
        if upload_date:
            info_dict['premiered'] = upload_date
            info_dict['aired'] = upload_date
        item.setInfo('video', info_dict)

    def _build_url(self, query: dict) -> str:
        """Constructs plugin URL for navigation."""
        return f"{self.base_url}?{urllib.parse.urlencode(query)}"

    def run(self):
        """Routes execution based on 'action' parameter."""
        action = self.params.get('action')

        if not action:
            self.menu_root()
        elif action == 'sort_menu':
            self.menu_sort_options()
        elif action == 'list_all_videos':
            self.menu_all_videos()
        elif action == 'list_series':
            self.menu_series()
        elif action == 'list_cast':
            self.menu_cast()
        elif action == 'list_years':
            self.menu_years()
        elif action == 'list_content_types':
            self.menu_content_types()
        elif action == 'list_filtered':
            self.menu_filtered()
        elif action == 'list_videos':
            self.menu_videos(self.params.get('slug', ''), self.params.get('title', ''))
        elif action == 'play':
            self.play_video(self.params.get('video_id', ''), self.params.get('title', ''))
        elif action == 'search':
            self.menu_search()
        elif action == 'jump_page':
            self.menu_jump_page()
        elif action == 'clear_resume':
            self.menu_clear_resume()
        else:
            if KODI_AVAILABLE:
                xbmc.log(f"[{ADDON_ID}] Unknown action: {action}", xbmc.LOGWARNING)
            if self.handle >= 0:
                xbmcplugin.endOfDirectory(self.handle, succeeded=False)

    def menu_root(self):
        """Displays top-level navigation menu with optional Resume shortcut."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        xbmcplugin.setContent(self.handle, 'files')

        # Check for persistent resume bookmark across restarts
        if self.remember_last_page:
            last_resume = self.nav_mgr.get_last_oldest() or self.nav_mgr.get_last_overall()
            if last_resume:
                page = last_resume.get('page', 1)
                total_pages = last_resume.get('total_pages', 0)
                title = last_resume.get('title', self._get_string(30100, 'All Videos'))
                if total_pages:
                    resume_tpl = self._get_string(30120, 'Resume: {title} (Page {page} of {total})')
                    resume_label = f">> " + resume_tpl.format(title=title, page=page, total=total_pages)
                else:
                    resume_tpl = self._get_string(30121, 'Resume: {title} (Page {page})')
                    resume_label = f"▶ " + resume_tpl.format(title=title, page=page)

                resume_plot = self._get_string(30122, 'Jump directly back to page {page} where you left off across Kodi restarts.').format(page=page)

                resume_item = xbmcgui.ListItem(label=resume_label)
                resume_item.setArt({
                    'icon': self.addon_icon,
                    'thumb': self.addon_icon,
                    'fanart': self.addon_fanart
                })
                self._set_video_info(resume_item, title=resume_label, plot=resume_plot)
                reset_label = self._get_string(30123, 'Reset Resume Bookmark to Page 1')
                resume_item.addContextMenuItems([
                    (reset_label, f"RunPlugin({self._build_url({'action': 'clear_resume', 'sort': 'oldest'})})")
                ])
                resume_url = self._build_url(last_resume.get('query', {}))
                xbmcplugin.addDirectoryItem(self.handle, resume_url, resume_item, isFolder=True)

        menu_items = [
            (self._get_string(30100, "All Videos"),
             {'action': 'sort_menu'},
             self._get_string(30101, "Browse all 4,899+ videos with chronological and custom sorting filters.")),
            (self._get_string(30102, "Browse by Series"),
             {'action': 'list_series'},
             self._get_string(30103, "Explore 40+ curated series (Demo Disk, Dude Soup, GTA 5, Wheelhaus, etc.).")),
            (self._get_string(30104, "Browse by Cast"),
             {'action': 'list_cast'},
             self._get_string(30105, "Browse videos featuring James, Bruce, Elyse, Adam, Lawrence, Jacob, and more.")),
            (self._get_string(30106, "Browse by Year"),
             {'action': 'list_years'},
             self._get_string(30107, "Browse complete archives year-by-year from 2015 to 2024.")),
            (self._get_string(30108, "Browse by Content Type"),
             {'action': 'list_content_types'},
             self._get_string(30109, "Filter by Gameplay, Podcasts, Full Episodes, Clips, Shorts, and Compilations.")),
            (self._get_string(30110, "Search Videos"),
             {'action': 'search'},
             self._get_string(30111, "Search through thousands of archived Funhaus episodes by title or cast.")),
        ]

        for label, query, plot in menu_items:
            item = xbmcgui.ListItem(label=label)
            item.setArt({
                'icon': self.addon_icon,
                'thumb': self.addon_icon,
                'fanart': self.addon_fanart
            })
            self._set_video_info(item, title=label, plot=plot)
            url = self._build_url(query)
            xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def menu_sort_options(self):
        """Displays sorting options matching funhausarchive.com #sort-filter with Resume shortcut."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        xbmcplugin.setContent(self.handle, 'files')

        # Check for saved position in Oldest First
        oldest_resume = self.nav_mgr.get_last_oldest() if self.remember_last_page else None
        if oldest_resume:
            page = oldest_resume.get('page', 1)
            total_pages = oldest_resume.get('total_pages', 0)
            if total_pages:
                resume_tpl = self._get_string(30120, 'Resume: {title} (Page {page} of {total})')
                resume_label = f">> " + resume_tpl.format(title=self._get_string(30140, "Oldest First"), page=page, total=total_pages)
            else:
                resume_tpl = self._get_string(30121, 'Resume: {title} (Page {page})')
                resume_label = f"▶ " + resume_tpl.format(title=self._get_string(30140, "Oldest First"), page=page)

            resume_item = xbmcgui.ListItem(label=resume_label)
            resume_item.setArt({
                'icon': self.addon_icon,
                'thumb': self.addon_icon,
                'fanart': self.addon_fanart
            })
            self._set_video_info(resume_item, title=resume_label, plot=self._get_string(30122, "Resume viewing directly from page {page}.").format(page=page))
            reset_label = self._get_string(30123, 'Reset Resume Bookmark to Page 1')
            resume_item.addContextMenuItems([
                (reset_label, f"RunPlugin({self._build_url({'action': 'clear_resume', 'sort': 'oldest'})})")
            ])
            resume_url = self._build_url(oldest_resume.get('query', {}))
            xbmcplugin.addDirectoryItem(self.handle, resume_url, resume_item, isFolder=True)

        oldest_label = self._get_string(30141, "Oldest First (Chronological) [From Page 1]") if oldest_resume else self._get_string(30140, "Oldest First (Chronological)")

        sort_options = [
            (oldest_label, "oldest", self._get_string(30142, "Watch the Funhaus archive in chronological order from February 2015 forward.")),
            (self._get_string(30143, "Newest First"), "newest", self._get_string(30144, "Most recently uploaded videos first.")),
            (self._get_string(30145, "Most Viewed"), "most-viewed", self._get_string(30146, "Highest all-time view counts.")),
            (self._get_string(30147, "Most Liked"), "most-liked", self._get_string(30148, "Fan-favorite videos with the most likes.")),
            (self._get_string(30149, "Longest First"), "longest", self._get_string(30150, "Longest podcasts, livestreams, and full gameplay recordings.")),
            (self._get_string(30151, "Shortest First"), "shortest", self._get_string(30152, "Quick clips, shorts, and highlights.")),
            (self._get_string(30153, "Title (A-Z)"), "title-az", self._get_string(30154, "Alphabetical order by video title.")),
            (self._get_string(30155, "Title (Z-A)"), "title-za", self._get_string(30156, "Reverse alphabetical order by video title.")),
            (self._get_string(30157, "Random / Shuffle"), "random", self._get_string(30158, "Random shuffle of the entire 4,900 video library.")),
        ]

        for label, sort_key, plot in sort_options:
            item = xbmcgui.ListItem(label=label)
            item.setArt({
                'icon': self.addon_icon,
                'thumb': self.addon_icon,
                'fanart': self.addon_fanart
            })
            self._set_video_info(item, title=label, plot=plot)
            url = self._build_url({'action': 'list_all_videos', 'sort': sort_key, 'page': '1'})
            xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def menu_all_videos(self):
        """Displays videos for the chosen sort order with pagination."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        sort_by = self.params.get('sort', 'oldest')
        page = int(self.params.get('page', 1))

        videos = self.scraper.filter_and_sort_videos(sort_by=sort_by)
        self._render_video_directory(
            videos=videos,
            page=page,
            base_query={'action': 'list_all_videos', 'sort': sort_by},
            view_title=f"{self._get_string(30100, 'All Videos')} ({sort_by})"
        )

    def menu_cast(self):
        """Displays all cast members with their total video count."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        xbmcplugin.setContent(self.handle, 'files')
        cast_list = self.scraper.get_cast_members()
        videos_word = self._get_string(30163, 'videos')

        for cast in cast_list:
            slug = cast.get('slug')
            name = cast.get('name', slug)
            count = cast.get('video_count', 0)
            label = f"{name} ({count:,} {videos_word})"

            item = xbmcgui.ListItem(label=label)
            item.setArt({
                'icon': self.addon_icon,
                'thumb': self.addon_icon,
                'fanart': self.addon_fanart
            })
            self._set_video_info(item, title=name, plot=f"Browse {count:,} Funhaus videos featuring {name}.")

            # Default to chronological (oldest) within cast
            url = self._build_url({
                'action': 'list_filtered',
                'cast': slug,
                'title': name,
                'sort': 'oldest',
                'page': '1'
            })
            xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def menu_years(self):
        """Displays available release years (2015–2024)."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        xbmcplugin.setContent(self.handle, 'files')
        years_list = self.scraper.get_years()
        videos_word = self._get_string(30163, 'videos')

        for yr in years_list:
            year = yr.get('year')
            count = yr.get('video_count', 0)
            label = f"{year} ({count:,} {videos_word})"

            item = xbmcgui.ListItem(label=label)
            item.setArt({
                'icon': self.addon_icon,
                'thumb': self.addon_icon,
                'fanart': self.addon_fanart
            })
            self._set_video_info(item, title=str(year), plot=f"Browse {count:,} Funhaus videos released in {year} in chronological order.")

            url = self._build_url({
                'action': 'list_filtered',
                'year': year,
                'title': f"{year}",
                'sort': 'oldest',
                'page': '1'
            })
            xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def menu_content_types(self):
        """Displays content types (Gameplay, Podcasts, Shorts, etc.)."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        xbmcplugin.setContent(self.handle, 'files')
        types_list = self.scraper.get_content_types()
        videos_word = self._get_string(30163, 'videos')

        for ct in types_list:
            slug = ct.get('slug')
            name = ct.get('name', slug)
            count = ct.get('video_count', 0)
            label = f"{name} ({count:,} {videos_word})"

            item = xbmcgui.ListItem(label=label)
            item.setArt({
                'icon': self.addon_icon,
                'thumb': self.addon_icon,
                'fanart': self.addon_fanart
            })
            self._set_video_info(item, title=name, plot=f"Browse {count:,} Funhaus {name} videos.")

            url = self._build_url({
                'action': 'list_filtered',
                'content_type': slug,
                'title': name,
                'sort': 'oldest',
                'page': '1'
            })
            xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def menu_filtered(self):
        """Displays videos filtered by Year, Cast, or Content Type."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        year = self.params.get('year')
        cast = self.params.get('cast')
        content_type = self.params.get('content_type')
        sort_by = self.params.get('sort', 'oldest')
        title = self.params.get('title', 'Filtered Videos')
        page = int(self.params.get('page', 1))

        videos = self.scraper.filter_and_sort_videos(
            sort_by=sort_by,
            year=year,
            cast=cast,
            content_type=content_type
        )

        base_query = {
            'action': 'list_filtered',
            'sort': sort_by,
            'title': title
        }
        if year: base_query['year'] = year
        if cast: base_query['cast'] = cast
        if content_type: base_query['content_type'] = content_type

        self._render_video_directory(
            videos=videos,
            page=page,
            base_query=base_query,
            view_title=title
        )

    def menu_series(self):
        """Displays list of all Funhaus series/shows."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        xbmcplugin.setContent(self.handle, 'tvshows')
        series_list = self.scraper.get_series()

        for series in series_list:
            slug = series.get('slug')
            title = series.get('title', slug)
            count = series.get('video_count', '')

            item = xbmcgui.ListItem(label=title, label2=count)
            item.setArt({
                'icon': self.addon_icon,
                'thumb': self.addon_icon,
                'fanart': self.addon_fanart
            })
            self._set_video_info(
                item,
                title=title,
                tvshowtitle=title,
                plot=f"{title} ({count}) from Funhaus Archive.",
                mediatype='tvshow'
            )

            url = self._build_url({
                'action': 'list_videos',
                'slug': slug,
                'title': title
            })
            xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def menu_videos(self, slug: str, series_title: str):
        """Displays list of videos belonging to a series."""
        if not KODI_AVAILABLE or self.handle < 0 or not slug:
            return

        page = int(self.params.get('page', 1))
        videos = self.scraper.get_series_videos(slug)

        self._render_video_directory(
            videos=videos,
            page=page,
            base_query={'action': 'list_videos', 'slug': slug, 'title': series_title},
            view_title=series_title
        )

    def _render_video_directory(self, videos: List[Dict[str, Any]], page: int, base_query: dict, view_title: str):
        """Helper to render a paginated list of videos with Jump and Persistence support."""
        xbmcplugin.setContent(self.handle, 'videos')

        total_videos = len(videos)
        if total_videos == 0:
            xbmcgui.Dialog().notification("Funhaus Archive", self._get_string(30161, "No videos found for this selection."), xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(self.handle, succeeded=True)
            return

        page_size = self.page_size
        if page_size > 0 and total_videos > page_size:
            total_pages = math.ceil(total_videos / page_size)
            page = max(1, min(page, total_pages))
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_videos)
            page_videos = videos[start_idx:end_idx]

            # Persist current page navigation position across Kodi restarts
            if self.remember_last_page:
                self.nav_mgr.save_position(
                    action=base_query.get('action', ''),
                    query=base_query,
                    page=page,
                    total_pages=total_pages,
                    title=view_title
                )

            # Build Jump-to-Page query
            jump_query = dict(base_query)
            jump_query['action'] = 'jump_page'
            jump_query['target_action'] = base_query.get('action', 'list_all_videos')
            jump_query['current_page'] = str(page)
            jump_query['total_pages'] = str(total_pages)
            jump_url = self._build_url(jump_query)

            # Previous Page Link
            if page > 1:
                prev_query = dict(base_query)
                prev_query['page'] = str(page - 1)
                prev_label = f"<< " + self._get_string(30125, 'Previous Page (Page {page} of {total})').format(page=page - 1, total=total_pages)
                prev_plot = self._get_string(30126, 'Go back to page {page}.').format(page=page - 1)
                prev_item = xbmcgui.ListItem(label=prev_label)
                prev_item.setArt({'icon': self.addon_icon, 'thumb': self.addon_icon, 'fanart': self.addon_fanart})
                self._set_video_info(prev_item, title=prev_label, plot=prev_plot)
                xbmcplugin.addDirectoryItem(self.handle, self._build_url(prev_query), prev_item, isFolder=True)

            # Top Jump to Page item for instant access without scrolling down
            jump_label = f"[ " + self._get_string(30127, 'Jump to Page... (Currently Page {page} of {total})').format(page=page, total=total_pages) + " ]"
            jump_plot = self._get_string(30128, 'Jump directly to any page number between 1 and {total}.').format(total=total_pages)
            jump_item_top = xbmcgui.ListItem(label=jump_label)
            jump_item_top.setArt({'icon': self.addon_icon, 'thumb': self.addon_icon, 'fanart': self.addon_fanart})
            self._set_video_info(jump_item_top, title=jump_label, plot=jump_plot)
            xbmcplugin.addDirectoryItem(self.handle, jump_url, jump_item_top, isFolder=True)
        else:
            total_pages = 1
            start_idx = 0
            end_idx = total_videos
            page_videos = videos

        # Render video items
        for video in page_videos:
            vid_id = video.get('id')
            title = video.get('title', f"Video {vid_id}")
            duration = video.get('duration', 0)
            upload_date = video.get('upload_date', '')
            thumb = video.get('thumbnail', self.addon_icon)
            backdrop = video.get('backdrop', self.addon_fanart)

            item = xbmcgui.ListItem(label=title)
            item.setArt({
                'icon': thumb,
                'thumb': thumb,
                'poster': thumb,
                'fanart': backdrop
            })

            plot_text = ""
            if upload_date:
                plot_text += f"Uploaded: {upload_date}\n"
            if video.get('view_count'):
                plot_text += f"Views: {video.get('view_count'):,} | "
            if video.get('like_count'):
                plot_text += f"Likes: {video.get('like_count'):,}\n"
            if video.get('cast_member_names'):
                plot_text += f"Cast: {', '.join(video.get('cast_member_names'))}\n"
            if video.get('description'):
                plot_text += f"\n{video.get('description')[:300]}"

            self._set_video_info(
                item,
                title=title,
                tvshowtitle=view_title,
                plot=plot_text.strip(),
                duration=duration,
                upload_date=upload_date,
                mediatype='video'
            )
            item.setProperty('IsPlayable', 'true')

            play_url = self._build_url({
                'action': 'play',
                'video_id': vid_id,
                'title': title
            })
            xbmcplugin.addDirectoryItem(self.handle, play_url, item, isFolder=False)

        # Bottom Pagination Controls
        if page_size > 0 and total_pages > 1:
            if end_idx < total_videos:
                next_query = dict(base_query)
                next_query['page'] = str(page + 1)
                next_label = self._get_string(30129, 'Next Page >> (Page {page} of {total}) [Showing {start}-{end} of {total_videos}]').format(
                    page=page + 1, total=total_pages, start=start_idx + 1, end=end_idx, total_videos=f"{total_videos:,}"
                )
                next_plot = self._get_string(30130, 'Proceed to page {page} of {total}.').format(page=page + 1, total=total_pages)
                next_item = xbmcgui.ListItem(label=next_label)
                next_item.setArt({'icon': self.addon_icon, 'thumb': self.addon_icon, 'fanart': self.addon_fanart})
                self._set_video_info(next_item, title=next_label, plot=next_plot)
                xbmcplugin.addDirectoryItem(self.handle, self._build_url(next_query), next_item, isFolder=True)

            jump_label = f"[ " + self._get_string(30127, 'Jump to Page... (Currently Page {page} of {total})').format(page=page, total=total_pages) + " ]"
            jump_plot = self._get_string(30128, 'Jump directly to any page number between 1 and {total}.').format(total=total_pages)
            jump_item_bottom = xbmcgui.ListItem(label=jump_label)
            jump_item_bottom.setArt({'icon': self.addon_icon, 'thumb': self.addon_icon, 'fanart': self.addon_fanart})
            self._set_video_info(jump_item_bottom, title=jump_label, plot=jump_plot)
            xbmcplugin.addDirectoryItem(self.handle, jump_url, jump_item_bottom, isFolder=True)

        xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def menu_jump_page(self):
        """Prompts for target page number with a numeric keypad dialog and updates directory container directly."""
        target_action = self.params.get('target_action', 'list_all_videos')
        try:
            total_pages = int(self.params.get('total_pages', '1'))
        except (ValueError, TypeError):
            total_pages = 1
        try:
            current_page = int(self.params.get('current_page', '1'))
        except (ValueError, TypeError):
            current_page = 1

        if not KODI_AVAILABLE:
            return

        dialog = xbmcgui.Dialog()
        heading = self._get_string(30131, 'Jump to Page (1 - {total}):').format(total=total_pages)
        entered = dialog.numeric(0, heading, str(current_page))
        if entered and entered.isdigit():
            target_page = max(1, min(int(entered), total_pages))
            dest_params = {k: v for k, v in self.params.items() if k not in ('action', 'target_action', 'total_pages', 'current_page')}
            dest_params['action'] = target_action
            dest_params['page'] = str(target_page)
            target_url = self._build_url(dest_params)
            # Update container directory directly so jump_page action is not left in Kodi history stack
            xbmc.executebuiltin(f"Container.Update({target_url})")
        else:
            # End directory gracefully if canceled
            if self.handle >= 0:
                xbmcplugin.endOfDirectory(self.handle, succeeded=False)

    def menu_clear_resume(self):
        """Resets the saved resume bookmark back to Page 1."""
        sort_key = self.params.get('sort', 'oldest')
        self.nav_mgr.clear_resume(sort_key)
        if KODI_AVAILABLE:
            msg = self._get_string(30124, "Resume bookmark reset to Page 1")
            xbmcgui.Dialog().notification("Funhaus Archive", msg, xbmcgui.NOTIFICATION_INFO)
            xbmc.executebuiltin("Container.Refresh")
        elif self.handle >= 0:
            xbmcplugin.endOfDirectory(self.handle, succeeded=True)

    def play_video(self, video_id: str, title: str):
        """Resolves video URL and initiates playback."""
        if not KODI_AVAILABLE or not video_id:
            return

        xbmc.log(f"[{ADDON_ID}] Resolving playback for video: {video_id} ({title})", xbmc.LOGINFO)
        resolved_url = self.resolver.resolve(video_id)

        if not resolved_url:
            err_msg = self._get_string(30162, "Failed to resolve video stream")
            xbmcgui.Dialog().notification("Funhaus Archive", err_msg, xbmcgui.NOTIFICATION_ERROR)
            if self.handle >= 0:
                xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem())
            return

        play_item = xbmcgui.ListItem(path=resolved_url)
        self._set_video_info(play_item, title=title)
        if self.handle >= 0:
            xbmcplugin.setResolvedUrl(self.handle, True, play_item)
        else:
            xbmc.Player().play(resolved_url, play_item)

    def menu_search(self):
        """Handles video search across the complete 4,899+ video archive."""
        if not KODI_AVAILABLE or self.handle < 0:
            return

        prompt = self._get_string(30160, 'Search Funhaus Archive')
        keyboard = xbmc.Keyboard('', prompt)
        keyboard.doModal()

        if keyboard.isConfirmed():
            query = keyboard.getText().strip()
            if query:
                # Search entire archive sorted chronologically
                matches = self.scraper.filter_and_sort_videos(sort_by='oldest', query=query)
                self._render_video_directory(
                    videos=matches,
                    page=1,
                    base_query={'action': 'search', 'query': query},
                    view_title=f"{self._get_string(30110, 'Search')}: {query}"
                )
            else:
                xbmcplugin.endOfDirectory(self.handle, succeeded=False)


def run(argv: list = None):
    """Entry point for the add-on router."""
    if argv is None:
        argv = sys.argv

    if len(argv) >= 3:
        addon = FunhausAddon(argv[0], argv[1], argv[2])
    else:
        # Standalone invocation fallback
        addon = FunhausAddon("plugin://plugin.video.funhausarchive/", "0", "")
    addon.run()


if __name__ == '__main__':
    run(sys.argv)
