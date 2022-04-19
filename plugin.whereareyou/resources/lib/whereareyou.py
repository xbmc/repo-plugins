import xbmc
import xbmcgui
import xbmcplugin
import json
import os
import sys
from resources.lib.waysettings import loadSettings
from resources.lib.xlogger import Logger
from resources.lib.api.harmony import HubControl
from resources.lib.api.url import URL
try:
    from urllib.parse import unquote_plus as _unquote_plus
except ImportError:
    from urllib import unquote_plus as _unquote_plus


def _upgrade():
    settings = loadSettings()
    if settings['version_upgrade'] != settings['ADDONVERSION']:
        settings['ADDON'].setSetting(
            'version_upgrade', settings['ADDONVERSION'])


class Main:

    def __init__(self):
        self._init_vars()
        self.LW = Logger(preamble='[Where Are You]',
                         logdebug=self.SETTINGS['debug'])
        self.LW.log(['script version %s started' %
                    self.SETTINGS['ADDONVERSION']], xbmc.LOGINFO)
        self._parse_argv()
        if self.TITLE and self.MESSAGE:
            self._display_dialog()
        elif self.SETTINGS['harmonycontrol']:
            self._mappings_options()
            if self.FROMSETTINGS:
                self.SETTINGS['ADDON'].openSettings()
        self.LW.log(['script stopped'], xbmc.LOGINFO)

    def _display_dialog(self):
        use_extended_dialog = False
        try:
            json_mappings = json.loads(self.SETTINGS['mappings'])
        except ValueError:
            json_mappings = {}
        if json_mappings and self.SETTINGS['harmonycontrol']:
            for item in json_mappings:
                thematch = json_mappings.get(item, {}).get('match', '')
                self.LW.log(['checking for %s in %s' % (thematch, self.TITLE)])
                self.LW.log(['checking for %s in %s' %
                            (thematch, self.MESSAGE)])
                if thematch.lower() in self.TITLE.lower() or thematch.lower() in self.MESSAGE.lower():
                    self.LW.log(['found match'])
                    activity, cmds = self._get_mapping_details(
                        json_mappings, item)
                    self.MESSAGE = '%s\n%s' % (
                        self.MESSAGE, self.SETTINGS['ADDONLANGUAGE'](32303))
                    use_extended_dialog = True
                    break
        if use_extended_dialog:
            if self.DIALOG.yesno(self.TITLE, self.MESSAGE):
                self._run_activity(activity, cmds)
        else:
            self.DIALOG.ok(self.TITLE, self.MESSAGE)
        pluginhandle = int(sys.argv[1])
        xbmcplugin.setContent(pluginhandle, 'files')
        play_item = xbmcgui.ListItem(path=os.path.join(
            self.SETTINGS['ADDONPATH'], 'resources', 'blank.mp4'))
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=play_item)

    def _init_vars(self):
        self.SETTINGS = loadSettings()
        self.DIALOG = xbmcgui.Dialog()
        if self.SETTINGS['harmonycontrol']:
            if self.SETTINGS['controltype'] == 1:
                if self.SETTINGS['ha_secure']:
                    conntype = 'https'
                else:
                    conntype = 'http'
                headers = {}
                headers['Content-Type'] = 'application/json'
                headers['Accept'] = 'application/json'
                headers['Authorization'] = 'Bearer %s' % self.SETTINGS['ha_token']
                self.JSONURL = URL('json', headers=headers)
                self.RESTURL = '%s://%s:%s/api/services' % (
                    conntype, self.SETTINGS['hub_ip'], self.SETTINGS['hub_port'])
            elif self.SETTINGS['controltype'] == 2:
                self.MYHUB = HubControl(
                    self.SETTINGS['hub_ip'], thetimeout=self.SETTINGS['timeout'], delay=self.SETTINGS['delay'])

    def _get_hascripts(self):
        script_list = []
        status, loglines, results = self.JSONURL.Get(self.RESTURL)
        self.LW.log(loglines)
        for domain in results:
            self.LW.log(['checking domain %s' % domain["domain"]])
            if domain["domain"] == 'script':
                for script_name in domain["services"]:
                    self.LW.log(['checking script %s' % script_name])
                    if not script_name in {'reload', 'turn_on', 'turn_off', 'toggle'}:
                        self.LW.log(['saving script'])
                        script_list.append(script_name)
                break
        script_list.sort()
        return script_list

    def _get_mappings(self):
        self.LW.log(['the settings mappings are:', self.SETTINGS['mappings']])
        try:
            json_mappings = json.loads(self.SETTINGS['mappings'])
        except ValueError:
            json_mappings = {}
        saved_mappings = []
        for item in json_mappings:
            mapping_name = json_mappings.get(item, {}).get('match')
            if mapping_name:
                saved_mappings.append(mapping_name)
        saved_mappings.sort()
        self.LW.log(['returning saved mappings of:', saved_mappings,
                    'returning json mappings of:', json_mappings])
        return saved_mappings, json_mappings

    def _get_mapping_details(self, json_mappings, item):
        activity = json_mappings.get(item, {}).get('activity', '')
        if self.SETTINGS['harmonyadvanced'] and self.SETTINGS['controltype'] == 2:
            cmds = json_mappings.get(item, {}).get('cmds', '')
        else:
            cmds = ''
        return activity, cmds

    def _mappings_options(self):
        options = [self.SETTINGS['ADDONLANGUAGE'](32300)]
        options.append(self.SETTINGS['ADDONLANGUAGE'](32301))
        options.append(self.SETTINGS['ADDONLANGUAGE'](32302))
        ret = self.DIALOG.select(
            self.SETTINGS['ADDONLANGUAGE'](32200), options)
        self.LW.log(['got back %s from the dialog box' % str(ret)])
        if ret == -1:
            return
        if ret == 0:
            self._option_add()
        elif ret == 1:
            self._option_edit()
        elif ret == 2:
            self._option_edit(dodelete=True)

    def _option_add(self, default_match='', default_activity='', default_cmds=''):
        thematch = self.DIALOG.input(
            self.SETTINGS['ADDONLANGUAGE'](32201), defaultt=default_match)
        if not thematch:
            return
        cmds = ''
        activity_list = []
        if self.SETTINGS['controltype'] == 1:
            activity_list = self._get_hascripts()
        elif self.SETTINGS['controltype'] == 2:
            activities, loglines = self.MYHUB.getActivities()
            self.LW.log(loglines)
            for activity_key in activities:
                activity_list.append(activity_key)
            activity_list.sort()
        if activity_list:
            try:
                default_index = activity_list.index(default_activity)
            except ValueError:
                default_index = -1
            ret = self.DIALOG.select(
                self.SETTINGS['ADDONLANGUAGE'](32203), activity_list, 0, default_index)
            if ret == -1:
                return
            else:
                activity = activity_list[ret]
        else:
            activity = self.DIALOG.input(
                self.SETTINGS['ADDONLANGUAGE'](32203), defaultt=default_activity)
        if self.SETTINGS['controltype'] == 2 and self.SETTINGS['harmonyadvanced']:
            cmds = self.DIALOG.input(
                self.SETTINGS['ADDONLANGUAGE'](32202), defaultt=default_cmds)
        saved_mappings, json_mappings = self._get_mappings()
        json_mappings[thematch] = {'match': thematch,
                                   'activity': activity, 'cmds': cmds}
        self.SETTINGS['ADDON'].setSetting(
            'mappings', json.dumps(json_mappings))

    def _option_edit(self, dodelete=False):
        saved_mappings, json_mappings = self._get_mappings()
        if not json_mappings:
            self._option_add()
            return
        ret = self.DIALOG.select(
            self.SETTINGS['ADDONLANGUAGE'](32204), saved_mappings)
        if ret == -1:
            return
        if dodelete:
            del json_mappings[saved_mappings[ret]]
            self.SETTINGS['ADDON'].setSetting(
                'mappings', json.dumps(json_mappings))
        else:
            thematch = json_mappings.get(
                saved_mappings[ret], {}).get('match', '')
            activity = json_mappings.get(
                saved_mappings[ret], {}).get('activity', '')
            cmds = json_mappings.get(saved_mappings[ret], {}).get('cmds', '')
            self._option_add(default_match=thematch,
                             default_activity=activity, default_cmds=cmds)

    def _parse_argv(self):
        try:
            check_from = sys.argv[1]
        except IndexError:
            check_from = ''
        if check_from == 'fromsettings':
            self.FROMSETTINGS = True
            self.TITLE = ''
            self.MESSAGE = ''
            return
        self.FROMSETTINGS = False
        try:
            params = dict(arg.split("=") for arg in sys.argv[2].split("&"))
        except IndexError:
            params = {}
        except Exception as e:
            self.LW.log(['no arguments found: %s' % e])
            params = {}
        self.TITLE = _unquote_plus(params.get('title', ''))
        self.MESSAGE = _unquote_plus(params.get('message', ''))

    def _run_activity(self, activity, cmds):
        if self.SETTINGS['controltype'] == 1:
            self.LW.log(['the HA script to run is: %s' % activity])
            if activity:
                payload = {"entity_id": "script.%s" % activity}
                theurl = self.RESTURL + '/script/' + activity
                status, loglines, results = self.JSONURL.Post(
                    theurl, data=json.dumps(payload))
                self.LW.log(loglines)
        elif self.SETTINGS['controltype'] == 2:
            self.LW.log(['the activity to run is: %s' % activity])
            if activity:
                result, loglines = self.MYHUB.startActivity(activity)
                self.LW.log(loglines)
                self.LW.log(['the result from the hub was:', result])
            else:
                self.LW.log(['no activity to run'])
            self.LW.log(['the extra commands to run are: %s' % cmds])
            if cmds:
                result, loglines = self.MYHUB.runCommands(cmds)
                self.LW.log(loglines)
                self.LW.log(['the result from the hub was:', result])
            else:
                self.LW.log(['no extra commands to run'])
        else:
            self.LW.log(['no hub IP address in settings'], xbmc.LOGWARNING)
