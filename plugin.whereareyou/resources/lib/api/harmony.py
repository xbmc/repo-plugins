# 0.1.4

import json
import websocket
from . import url
try:
    import xbmc
    MONITOR = xbmc.Monitor()
except:
    MONITOR = None
    import time


class HubControl:

    def __init__(self, hub_ip, thetimeout=30, delay=250):
        self.HUBIP = hub_ip
        self.TIMEOUT = thetimeout
        self.DELAY = delay / 1000
        self.HUBID = ''
        self.CONFIG = {}
        self.COMMANDS = {}
        self.LOGLINES = []
        self.WSURL = 'ws://%s:8088/?domain=svcs.myharmony.com&hubId=' % self.HUBIP

    def getActivities(self, excludes=None):
        self._init_vars()
        activities = self._get_activities()
        self.LOGLINES.extend(['the activities are:', activities])
        if excludes:
            for item in excludes:
                del activities[item]
        return activities, self.LOGLINES

    def runCommands(self, cmds_str):
        self._init_vars()
        self.LOGLINES.extend(['the commands passed in are: %s' % cmds_str])
        results = []
        r_cmds = self._parse_cmds(cmds_str)
        for r_cmd in r_cmds:
            if r_cmd == 'pause':
                if MONITOR:
                    if MONITOR.waitForAbort(self.DELAY):
                        return [], self.LOGLINES
                else:
                    time.sleep(self.DELAY)
                continue
            hub_cmd = {}
            hub_cmd['cmd'] = 'vnd.logitech.harmony/vnd.logitech.harmony.engine?holdAction'
            hub_cmd['id'] = '0'
            hub_cmd['params'] = {'status': 'press',
                                 'timestamp': 0, 'verb': 'render', 'action': r_cmd}
            cmd = {}
            cmd['hubId'] = self.HUBID
            cmd['timeout'] = self.TIMEOUT
            cmd['hbus'] = hub_cmd
            self._query_hub(cmd, buttonpress=True)
        return results, self.LOGLINES

    def startActivity(self, activity):
        self._init_vars()
        self.LOGLINES.append('the activity passed in is %s' % activity)
        activities = self._get_activities()
        activity_id = activities.get(activity.strip(), {}).get('id', '')
        self.LOGLINES.append('the activity id is %s' % activity_id)
        if not activity_id:
            return None
        hub_cmd = {}
        hub_cmd['cmd'] = 'vnd.logitech.harmony/vnd.logitech.harmony.engine?startactivity'
        hub_cmd['id'] = '0'
        hub_cmd['params'] = {'async': 'true', 'timestamp': 0, 'args': {
            'rule': 'start'}, 'activityId': '%s' % activity_id}
        cmd = {}
        cmd['hubId'] = self.HUBID
        cmd['timeout'] = self.TIMEOUT
        cmd['hbus'] = hub_cmd
        result = self._query_hub(cmd)
        return result, self.LOGLINES

    def _init_vars(self):
        self.LOGLINES = []
        self._get_config()
        self._get_commands()

    def _get_activities(self):
        activities = {}
        for item in self.CONFIG.get('data', {}).get('activity', {}):
            label = item.get('label')
            theid = item.get('id')
            if label and theid:
                activities[label] = {'activity': label, 'id': str(theid)}
                self.LOGLINES.append(
                    'added activity %s with id of %s' % (label, theid))
        return activities

    def _get_commands(self):
        if self.COMMANDS:
            return
        for device in self.CONFIG.get('data', {}).get('device', []):
            device_name = device.get('label')
            if not device_name:
                break
            all_cmds = {}
            for control_group in device.get('controlGroup', []):
                for function in control_group.get('function', []):
                    cmd_name = function.get('name', '')
                    if not cmd_name:
                        break
                    all_cmds[cmd_name] = function.get('action', '')
            self.COMMANDS[device_name] = all_cmds
        self.LOGLINES.extend(
            ['the complete list of commands by device is:', self.COMMANDS])

    def _get_config(self):
        if self.CONFIG:
            return
        hub_cmd = {}
        hub_cmd['cmd'] = 'vnd.logitech.harmony/vnd.logitech.harmony.engine?config'
        hub_cmd['id'] = '0'
        hub_cmd['params'] = {'verb': 'get'}
        cmd = {}
        cmd['hubId'] = self.HUBID
        cmd['timeout'] = self.TIMEOUT
        cmd['hbus'] = hub_cmd
        self.CONFIG = self._query_hub(cmd)

    def _get_hubid(self):
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'utf-8'
        headers['Origin'] = 'http://sl.dhg.myharmony.com'
        jsonurl = url.URL('json', headers=headers)
        statuscode, loglines, res = jsonurl.Post(
            'http://%s:8088' % self.HUBIP, data='{"id":29549457,"cmd":"setup.account?getProvisionInfo","timeout":90000}')
        self.LOGLINES.extend(loglines)
        self.HUBID = str(res.get('data', {}).get('activeRemoteId'))
        self.LOGLINES.append(['the hub id is %s' % self.HUBID])

    def _parse_cmds(self, cmds_str):
        cmds = []
        r_cmds = cmds_str.split('|')
        self.LOGLINES.extend(['using command list of:', r_cmds])
        for r_cmd in r_cmds:
            item = r_cmd.split(':')
            try:
                device = item[0]
                button = item[1]
            except IndexError:
                device = ''
                button = ''
            cmd = self.COMMANDS.get(device.strip(), {}).get(
                button.strip(), 'pause')
            cmds.append(cmd)
        self.LOGLINES.extend(['returning cmds of:', cmds])
        return cmds

    def _query_hub(self, cmd, buttonpress=False):
        self.LOGLINES.extend(['the command is:', cmd])
        if not self.HUBID:
            self._get_hubid()
        ws = websocket.create_connection(
            self.WSURL + self.HUBID, timeout=self.TIMEOUT)
        ws.send(json.dumps(cmd))
        if not buttonpress:
            result = ws.recv()
        else:
            result = '{}'
        ws.close()
        return json.loads(result)
