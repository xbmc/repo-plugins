import math
from globals import *
from database import Database


class BuildGuide(threading.Thread):
    guide_days = int(ADDON.getSetting('epg_days'))
    guide_thread_1 = None
    guide_thread_2 = None
    guide_thread_3 = None
    guide_thread_4 = None
    keep_running = True
    monitor = xbmc.Monitor()
    update_interval = int(ADDON.getSetting('epg_interval')) * 3600
    update_on_start = ADDON.getSetting('epg_on_start')

    def __init__(self):
        threading.Thread.__init__(self)
        self.db = Database()

    def run(self):
        xbmc.log('BuildGuide: Thread starting....')

        first_time_thru = True
        if self.update_on_start == 'false':
            first_time_thru = False
            self.monitor.waitForAbort(self.update_interval)

        while not self.monitor.abortRequested():
            xbmc.log('BuildGuide: Looping through guide days....')
            # Build main guide longer w/ less info
            self.guide_thread_1 = threading.Thread(name='GuideThread 1', target=self.long_guide())

            while self.guide_thread_1.isAlive():
                xbmc.log('BuildGuide: Main guide thread active, waiting for finish')

            # Build short guide with more info
            channel_ids = []
            for channel_id, title, logo in self.db.get_db_channels():
                channel_ids.append(channel_id)

            third = int(math.ceil(len(channel_ids) / 3))
            self.guide_thread_2 = threading.Thread(name='GuideThread 2',
                                                   target=self.short_guide(channel_ids[:third]))
            self.guide_thread_3 = threading.Thread(name='GuideThread 3',
                                                   target=self.short_guide(channel_ids[third:third + third]))
            self.guide_thread_4 = threading.Thread(name='GuideThread 4',
                                                   target=self.short_guide(channel_ids[third + third:]))

            xbmc.log('BuildGuide: before loop')
            thread_alive = True
            while thread_alive:
                thread_alive = False
                if self.guide_thread_2.isAlive() or self.guide_thread_3.isAlive() or self.guide_thread_4.isAlive():
                    thread_alive = True
                    xbmc.log('BuildGuide: Active threads remain, waiting for finish')

                if self.monitor.waitForAbort(5):
                    break

            xbmc.log('BuildGuide: after loop')
            self.db.clean_db_epg()
            self.db.build_epg_xml()
            if first_time_thru:
                xbmc.log('BuildGuide: First time thru, toggling IPTV restart')
                pvr_toggle_off = '{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", ' \
                                 '"params": {"addonid": "pvr.iptvsimple", "enabled": false}, "id": 1}'
                pvr_toggle_on = '{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", ' \
                                '"params": {"addonid": "pvr.iptvsimple", "enabled": true}, "id": 1}'
                xbmc.executeJSONRPC(pvr_toggle_off)
                xbmc.executeJSONRPC(pvr_toggle_on)
                first_time_thru = False

            if self.monitor.waitForAbort(self.update_interval):
                break

    def long_guide(self):
        channel_ids = ''
        for channel_id, title, logo in self.db.get_db_channels():
            if channel_ids != '':
                channel_ids += ','
            channel_ids += channel_id

        url = 'https://epg-service.totsuko.tv/epg_service_sony/service/v2/airings'
        headers = {
            'Accept': '*/*',
            'reqPayload': PS_VUE_ADDON.getSetting(id='EPGreqPayload'),
            'User-Agent': UA_ANDROID_TV,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'com.snei.vue.android',
            'Connection': 'keep-alive',
            'Origin': 'https://vue.playstation.com',
            'Content-Type': 'application/json',
            'Referer': 'https://vue.playstation.com/watch/guide'
        }

        guide_start = self.db.get_last_start_time()
        if guide_start is None or guide_start == '':
            guide_start = datetime.utcnow() - timedelta(hours=1, minutes=datetime.utcnow().minute)

        date_diff = (datetime.utcnow() +
                     timedelta(minutes=(-1 * datetime.utcnow().minute), days=self.guide_days)) - guide_start
        guide_end = guide_start + date_diff

        payload = '{"start":"' + guide_start.strftime(DATE_FORMAT) + '","end":"' + guide_end.strftime(
            DATE_FORMAT) + '","channel_ids":[' + channel_ids + ']}'
        r = requests.post(url, headers=headers, cookies=load_cookies(), data=payload, verify=VERIFY)

        programs_list = []
        for program in r.json()['body']['airings']:
            programs_list.append(self.build_epg_channel(program))

        if programs_list:
            self.db.update_epg_info(programs_list)

    def short_guide(self, channel_ids):
        xbmc.log('BuildGuide: Thread started...')
        programs_list = []
        for channel in channel_ids:
            json_source = get_json(EPG_URL + '/timeline/live/' + channel + '/watch_history_size/0/coming_up_size/50')
            for strand in json_source['body']['strands']:
                if strand['id'] == 'now_playing' or strand['id'] == 'coming_up':
                    for program in strand['programs']:
                        programs_list.append(self.build_epg_channel(program))

        if programs_list:
            self.db.update_epg_info(programs_list)

    def build_epg_channel(self, program):
        if 'start' in program:
            start_time = string_to_date(program['start'], DATE_FORMAT)
        elif 'airings' in program and 'airing_date' in program['airings'][0]:
            start_time = string_to_date(program['airings'][0]['airing_date'], DATE_FORMAT)
        start_time = start_time.strftime("%Y%m%d%H%M%S")

        if 'end' in program:
            stop_time = string_to_date(program['end'], DATE_FORMAT)
        elif 'airings' in program and 'airing_enddate' in program['airings'][0]:
            stop_time = string_to_date(program['airings'][0]['airing_enddate'], DATE_FORMAT)
        stop_time = stop_time.strftime("%Y%m%d%H%M%S")

        if 'channel_id' in program:
            channel_id = str(program['channel_id'])
        elif 'channel' in program and 'channel_id' in program['channel']:
            channel_id = str(program['channel']['channel_id'])

        title = program['title']

        title_sub = ''
        if 'title_sub' in program:
            title_sub = program['title_sub']

        desc = ''
        if 'synopsis' in program:
            desc = program['synopsis']
            desc = desc

        icon = ''
        if 'urls' in program:
            for image in program['urls']:
                if 'width' in image:
                    if image['width'] == 600 or image['width'] == 440:
                        icon = image['src']
                        break

        genre = ''
        if 'genres' in program:
            for item in program['genres']:
                if genre != '':
                    genre += ','
                genre += item['genre']

        return start_time, stop_time, channel_id, title, title_sub, desc, icon, genre

    def stop(self):
        xbmc.log('BuildGuide: Stop triggered....')
        self.keep_running = False
        self.join(0)
