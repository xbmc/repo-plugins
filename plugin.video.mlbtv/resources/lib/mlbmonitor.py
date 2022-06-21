from resources.lib.utils import Util
from resources.lib.globals import *

class MLBMonitor(xbmc.Monitor):
    stream_started = False
    stream_start_tries = 5
    verify = True
    broadcast_start_timestamp = None

    def __init__(self, *args, **kwargs):
        xbmc.log("MLB Monitor init")
        self.monitor = xbmc.Monitor()

    # override the onSettingsChanged method to detect if a new MLB monitor has started (so we can close this one)
    def onSettingsChanged(self):
        xbmc.log("MLB Monitor detected settings changed")
        settings = xbmcaddon.Addon(id='plugin.video.mlbtv')
        new_mlb_monitor_started = str(settings.getSetting(id="mlb_monitor_started"))
        if self.mlb_monitor_started != new_mlb_monitor_started:
            xbmc.log("MLB Monitor from " + self.mlb_monitor_started + " closing due to another monitor starting on " + new_mlb_monitor_started)
            self.mlb_monitor_started = ''

    def skip_monitor(self, skip_type, game_pk, broadcast_start_timestamp, is_live, start_inning, start_inning_half):
        xbmc.log("Skip monitor for " + game_pk + " starting")

        self.mlb_monitor_started = str(datetime.now())
        settings.setSetting(id='mlb_monitor_started', value=self.mlb_monitor_started)
        xbmc.log("Skip monitor for " + game_pk + " started at " + self.mlb_monitor_started)

        # initialize player to monitor play time
        player = xbmc.Player()
        last_time = None

        # fetch skip markers
        skip_markers = self.get_skip_markers(skip_type, game_pk, broadcast_start_timestamp, 0, start_inning, start_inning_half)
        xbmc.log('Skip monitor for ' + game_pk + ' skip markers : ' + str(skip_markers))

        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(1):
                xbmc.log("Skip monitor for " + game_pk + " aborting")
                break
            elif len(skip_markers) == 0:
                xbmc.log("Skip monitor for " + game_pk + " closing due to no more skip markers")
                break
            elif self.stream_started == True and not xbmc.getCondVisibility("Player.HasMedia"):
                xbmc.log("Skip monitor for " + game_pk + " closing due to stream stopped")
                break
            elif self.mlb_monitor_started == '':
                xbmc.log("Skip monitor for " + game_pk + " closing due to reset")
                break
            elif xbmc.getCondVisibility("Player.HasMedia"):
                if self.stream_started == False:
                    xbmc.log("Skip monitor for " + game_pk + " detected stream start")
                    self.stream_started = True
                    # just for fun, we can log our stream duration, to compare it against skip time detected
                    if start_inning == 0:
                        try:
                            total_stream_time = player.getTotalTime()
                            xbmc.log('Skip monitor for ' + game_pk + ' total stream time ' + str(timedelta(seconds=total_stream_time)))
                        except:
                            pass
                current_time = player.getTime()
                # make sure we're not paused, and current time is valid (less than 10 hours) -- sometimes Kodi was returning a crazy large current time as the stream was starting
                if current_time > 0 and current_time != last_time and current_time < 36000:
                    last_time = current_time
                    # remove any past skip markers so user can seek backward freely
                    while len(skip_markers) > 0 and current_time > skip_markers[0][1]:
                        xbmc.log("Skip monitor for " + game_pk + " removed skip marker at " + str(skip_markers[0][1]) + ", before current time " + str(current_time))
                        skip_markers.pop(0)
                    # seek to end of break if we fall within skip marker range, then remove marker so user can seek backward freely
                    if len(skip_markers) > 0 and current_time >= skip_markers[0][0] and current_time < skip_markers[0][1]:
                        xbmc.log("Skip monitor for " + game_pk + " processed skip marker at " + str(skip_markers[0][1]))
                        player.seekTime(skip_markers[0][1])
                        skip_markers.pop(0)
                        # since we just processed a skip marker, we can delay further processing a little bit
                        xbmc.sleep(2000)
                    # if we've run out of skip markers and it's a live event and we're skipping things, check for more
                    if len(skip_markers) == 0 and is_live == True and skip_type > 0:
                        # refresh current time, and look ahead slightly
                        current_time = player.getTime() + 10
                        xbmc.log('Skip monitor for ' + game_pk + ' refreshing skip markers from ' + str(current_time))
                        skip_markers = self.get_skip_markers(skip_type, game_pk, broadcast_start_timestamp, current_time)
                        xbmc.log('Skip monitor for ' + game_pk + ' refreshed skip markers : ' + str(skip_markers))
            else:
                if self.stream_started == False:
                    xbmc.log("Skip monitor for " + game_pk + " waiting for stream to start")
                    self.stream_start_tries -= 1
                    if self.stream_start_tries < 1:
                        xbmc.log("Skip monitor for " + game_pk + " closing due to stream not starting")
                        break

        xbmc.log("Skip monitor for " + game_pk + " closed")


    # get the gameday data, which contains the event timestamps
    def get_gameday_data(self, game_pk):
        xbmc.log('Skip monitor for ' + game_pk + ' getting gameday data')

        url = API_URL + '/api/v1.1/game/' + game_pk + '/feed/live'
        headers = {
            'User-agent': UA_PC,
            'Origin': 'https://www.mlb.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-type': 'application/json'
        }
        r = requests.get(url, headers=headers, verify=self.verify)
        json_source = r.json()
        return json_source


    # calculate skip markers from gameday events
    def get_skip_markers(self, skip_type, game_pk, broadcast_start_timestamp, current_time=0, start_inning=0, start_inning_half='top'):
        xbmc.log('Skip monitor for ' + game_pk + ' getting skip markers for skip type ' + str(skip_type))
        if current_time > 0:
            xbmc.log('Skip monitor for ' + game_pk + ' searching beyond ' + str(current_time))

        # initialize our list of skip times
        skip_markers = []

        json_source = self.get_gameday_data(game_pk)

        # calculate total skip time (for fun)
        total_skip_time = 0

        # make sure we have play data
        if 'liveData' in json_source and 'plays' in json_source['liveData'] and 'allPlays' in json_source['liveData']['plays']:
            # assume the game starts in a break
            break_start = 0

            # keep track of inning, if skipping inning breaks only
            previous_inning = 0
            previous_inning_half = None

            # make sure start inning is valid
            if start_inning > 0:
                last_play_index = len(json_source['liveData']['plays']['allPlays']) - 1
                final_inning = json_source['liveData']['plays']['allPlays'][last_play_index]['about']['inning']
                if start_inning >= final_inning:
                    if start_inning > final_inning:
                        start_inning = final_inning
                    final_inning_half = json_source['liveData']['plays']['allPlays'][last_play_index]['about']['halfInning']
                    if start_inning_half == 'bottom' and final_inning_half == 'top':
                        start_inning_half = final_inning_half

            # loop through all plays
            for play in json_source['liveData']['plays']['allPlays']:
                # exit loop after found inning, if not skipping any breaks
                if skip_type == 0 and len(skip_markers) == 1:
                    break
                current_inning = play['about']['inning']
                current_inning_half = play['about']['halfInning']
                # make sure we're past our start inning
                if current_inning > start_inning or (current_inning == start_inning and (current_inning_half == start_inning_half or current_inning_half == 'bottom')):
                    # loop through events within each play
                    for index, playEvent in enumerate(play['playEvents']):
                        # default to longer action end padding
                        event_end_padding = ACTION_END_PADDING
                        # always exclude break types
                        if 'event' in playEvent['details'] and playEvent['details']['event'] in BREAK_TYPES:
                            # if we're in the process of skipping inning breaks, treat the first break type we find as another inning break
                            if skip_type == 1 and previous_inning > 0:
                                break_start = (parse(playEvent['startTime']) - broadcast_start_timestamp).total_seconds() + event_end_padding
                                previous_inning = 0
                            continue
                        else:
                            # for non-action plays, use shorter pitch end padding instead
                            if index < (len(play['playEvents'])-1) and ('details' not in playEvent or 'event' not in playEvent['details'] or not any(substring in playEvent['details']['event'] for substring in ACTION_TYPES)):
                                event_end_padding = PITCH_END_PADDING
                            action_index = None
                            # skip type 1 (breaks) and 2 (idle time) will look at all plays with an endTime
                            if skip_type <= 2 and 'endTime' in playEvent:
                                action_index = index
                            elif skip_type == 3:
                                # skip type 3 excludes non-action pitches (events that aren't last in the at-bat and don't fall under action types)
                                if index < (len(play['playEvents'])-1) and ('details' not in playEvent or 'event' not in playEvent['details'] or not any(substring in playEvent['details']['event'] for substring in ACTION_TYPES)):
                                    continue
                                else:
                                    # if the action is associated with another play or the event doesn't have an end time, use the previous event instead
                                    if ('actionPlayId' in playEvent or 'endTime' not in playEvent) and index > 0:
                                        action_index = index - 1
                                    else:
                                        action_index = index
                            if action_index is None:
                                continue
                            else:
                                break_end = (parse(play['playEvents'][action_index]['startTime']) - broadcast_start_timestamp).total_seconds() + EVENT_START_PADDING
                                # if the break end should be greater than the current playback time
                                # and the break duration should be greater than than our specified minimum
                                # and if skip type is not 1 (inning breaks) or the inning has changed
                                # then we'll add the skip marker
                                # otherwise we'll ignore it and move on to the next one
                                if break_end > current_time and (break_end - break_start) >= MINIMUM_BREAK_DURATION and (skip_type != 1 or current_inning != previous_inning or current_inning_half != previous_inning_half):
                                    skip_markers.append([break_start, break_end])
                                    total_skip_time += break_end - break_start
                                    previous_inning = current_inning
                                    previous_inning_half = current_inning_half
                                    # exit loop after found inning, if not skipping breaks
                                    if skip_type == 0:
                                        break
                                break_start = (parse(play['playEvents'][action_index]['endTime']) - broadcast_start_timestamp).total_seconds() + event_end_padding
                                # add extra padding for overturned review plays
                                if 'reviewDetails' in play:
                                    isOverturned = play['reviewDetails']['isOverturned']
                                    if isOverturned == False and 'additionalReviews' in play['reviewDetails'] and len(play['reviewDetails']['additionalReviews']) > 0:
                                        for additionalReview in play['reviewDetails']['additionalReviews']:
                                            isOverturned = additionalReview['isOverturned']
                                            if isOverturned == True:
                                                break
                                    if isOverturned == True:
                                        break_start += 40

        xbmc.log('Skip monitor for ' + game_pk + ' found ' + str(timedelta(seconds=total_skip_time)) + ' total skip time')

        return skip_markers
