'''
Inspired by code of Esteban Ordano

http://estebanordano.com/ted-talks-download-subtitles/
http://estebanordano.com.ar/wp-content/uploads/2010/01/TEDTalkSubtitles.py_.zip
'''

__friendly_message__ = 'Error showing subtitles'

class Subtitles:

    def __init__(self, fetcher, logger):
        self.fetcher = fetcher
        self.logger = logger

    def __format_time__(self, time):
        millis = time % 1000
        seconds = (time / 1000) % 60
        minutes = (time / 60000) % 60
        hours = (time / 3600000)
        return '%02d:%02d:%02d,%03d' % (hours, minutes, seconds, millis)

    def __format_subtitles__(self, subtitles, introDuration):
        result = ''
        for idx, sub in enumerate(subtitles):
            start = introDuration + sub['start']
            end = start + sub['duration']
            result += '%d\n%s --> %s\n%s\n\n' % (idx + 1, self.__format_time__(start), self.__format_time__(end), sub['content'])
        return result

    def __get_languages__(self, talk_json):
        '''
        Get languages for a talk, or empty array if we fail.
        '''
        return [l['languageCode'] for l in talk_json['player_talks'][0]['languages']]

    def get_subtitles(self, talk_id, language):
        url = 'https://www.ted.com/talks/subtitles/id/%s/lang/%s' % (talk_id, language)
        subs = self.fetcher.get(url).json()
        captions = []
        for caption in subs['captions']:
            captions += [{'start': caption['startTime'], 'duration': caption['duration'], 'content': caption['content']}]
        return captions

    def get_subtitles_for_talk(self, talk_json, accepted_languages):
        '''
        Return subtitles in srt format, or notify the user and return None if there was a problem.
        '''
        # TODO: Get subtitles using metadata.json reference https://hls.ted.com/project_masters/690/metadata.json?intro_master_id=2346

        try:
            talk_id = talk_json['id']
            languages = self.__get_languages__(talk_json)

            if len(languages) == 0:
                msg = 'No subtitles found'
                self.logger(msg, friendly_message=msg)
                return None

            language_matches = [l for l in accepted_languages if l in languages]
            if not language_matches:
                msg = 'No subtitles in: {}'.format(','.join(accepted_languages))
                self.logger(msg, friendly_message=msg)
                return None

            raw_subtitles = self.get_subtitles(talk_id, language_matches[0])
            if not raw_subtitles:
                return None

            metadata_url = talk_json['player_talks'][0]['resources']['hls']['metadata']
            metadata_json = self.fetcher.get(metadata_url).json()
            # TED hls supports VTT subtitles, which appear to be correctly timed, but Kodi does not.
            # For now continue to use old API, though I expect we'll need to switch to scraping the VTT subtitles at some point.
            intro_duration = None
            if 'domains' in metadata_json:
                intro_duration = int(metadata_json['domains'][0]['duration'] * 1000)
            elif 'timing' in metadata_json:
                intro_duration = int(metadata_json['timing']['content']['start'] * 1000)
            else:
                raise Exception('Cannot parse hls metadata')

            intro_duration -= 1000 # FIXME: subtitles seem to lag video when doing m3u8 playback in matrix

            return self.__format_subtitles__(raw_subtitles, intro_duration)

        except Exception as e:
            # Graceful degradation: let video play without subtitles.
            self.logger('Could not display subtitles: {}'.format(e), friendly_message=__friendly_message__)
            return None
