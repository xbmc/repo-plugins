from xbmcgui import Dialog
from tmdbhelper.lib.addon.plugin import get_localized
from copy import deepcopy


ACTION_RULES = {
    'title': {'default': '{title}'},
    'year': {'default': '{year}'},
    'originaltitle': {'default': '{originaltitle}'},
    'imdbnumber': {'default': '{imdb}'},
    'premiered': {'default': '{premiered}'},
    'firstaired': {'default': '{showpremiered}'},
    'season': {'default': '{season}'},
    'episode': {'default': '{episode}'},
    'label': {'default': '{title}'},
    'file': {},
    'showtitle': {'default': '{showname}'},
    'position': {},
    'keyboard': {},
    'dialog': {'default': 'auto', 'options': ['true', 'auto']},
    'strict': {'default': 'true', 'options': ['true']},
    'return': {'default': 'true', 'options': ['true']},
}


ACTION_VALUES = [
    '{id}', '{tmdb}', '{imdb}', '{tvdb}', '{trakt}', '{slug}', '{name}', '{year}',
    '{season}', '{episode}', '{premiered}', '{released}', '{showname}', '{showyear}',
    '{showpremiered}', '{clearname}', '{thumbnail}', '{poster}', '{fanart}', '{title}',
    '{originaltitle}', '{epid}', '{epimdb}', '{eptmdb}', '{eptrakt}', '{now}'
]


class _EditPlayer():
    def __init__(self, player, filename):
        self.player = player
        self.filename = filename
        self._dialogsettings = [
            {
                'name': lambda: f'play_movie',
                'func': lambda: self.configure_steps('play_movie'),
            },
            {
                'name': lambda: f'play_episode',
                'func': lambda: self.configure_steps('play_episode'),
            },
            {
                'name': lambda: f'search_movie',
                'func': lambda: self.configure_steps('search_movie'),
            },
            {
                'name': lambda: f'search_episode',
                'func': lambda: self.configure_steps('search_episode'),
            },
        ]

    def _edit_keymatch_step(self, action, header):

        def _add_keymatch_rule():
            """ Select rule or listitem key to match """
            _dialogkeys = [i for i in ACTION_RULES]
            x = Dialog().select(get_localized(32444), _dialogkeys)
            if x == -1:
                return -1
            action.setdefault(_dialogkeys[x], ACTION_RULES[_dialogkeys[x]].get('default', ' '))
            return _dialogkeys[x]

        def _edit_keymatch_value(key, value):
            """ Select TMDbHelper value to match against """
            _dialogbuiltins = {
                'edit': lambda: Dialog().input(header, defaultt=value),
                'delete': lambda: None}
            _actionoption = ACTION_RULES[key].get('options')
            if _actionoption:  # If there's pre-set options then the rule cannot be edited
                _dialogbuiltins.pop('edit')
            _dialogvalues = [i for i in _dialogbuiltins]
            _dialogvalues += _actionoption or ACTION_VALUES
            x = Dialog().select(get_localized(32443).format(key), _dialogvalues)
            if x == -1:  # If user cancelled we return the old value
                return value
            new_value = _dialogvalues[x]
            return _dialogbuiltins[new_value]() if new_value in _dialogbuiltins else new_value

        _keys = [k for k in action.keys()]
        _dialogitems = [f'{k}: {action[k]}' for k in _keys]
        _dialogitems += [get_localized(32442), get_localized(192), get_localized(190)]
        x = Dialog().select(header, _dialogitems)

        preset = None
        if x == -1:  # User cancelled by pressing back
            return -1
        if _dialogitems[x] == get_localized(32442):  # Add new action
            key = _add_keymatch_rule()
            preset = action.get(key)
        elif _dialogitems[x] == get_localized(192):  # Clear actions
            key = -1
            action = {}
        elif _dialogitems[x] == get_localized(190):  # Save action
            return action
        else:  # Chose a key
            key = _keys[x]

        if key != -1:
            action[key] = preset or _edit_keymatch_value(key, action.get(key))
            if not action[key]:
                action.pop(key)
        return self._edit_keymatch_step(action, header)

    def edit_steps(self, actions, header):
        _dialogitems = [f'{i}' for i in actions]
        _dialogitems += [get_localized(32441), get_localized(190)]  # Add additional "new step" and save item

        # Choose the step to edit
        x = Dialog().select(header, _dialogitems)
        if x == -1:  # User cancelled
            return -1
        if _dialogitems[x] == get_localized(190):  # User wants to save
            return actions
        if _dialogitems[x] == get_localized(32441):  # User wants to add a new step
            if len(actions) == 0:  # No actions so needs a plugin path for search TODO: Add directory walk
                action = f'plugin://{self.player.get("plugin")}/'
            else:  # Init an empty action dictionary if not first step
                action = {}
        else:  # Set the selected step as our action to edit
            action = actions[x]

        # Edit the action
        if isinstance(action, str):  # First step is a string so we want to edit manually with keboard
            action = Dialog().input(get_localized(32446).format(header), defaultt=action)
        else:  # Else present dialog to edit rules
            action = self._edit_keymatch_step(deepcopy(action), header=get_localized(32445).format(x + 1))
        if action == -1:
            pass  # Do nothing as user cancelled
        elif x >= len(actions):
            actions.append(action)
        else:
            actions[x] = action
        if not action:  # Don't add empties. If user deleted all rules from step then delete it
            actions.pop(x)

        return self.edit_steps(actions, header=header)

    def configure_steps(self, action):
        actions = self.player.get(action)
        if not actions:
            return self.create_steps(action)
        if not isinstance(actions, list):
            actions = [actions]
        actions = self.edit_steps(deepcopy(actions), header=f'{self.filename} - {action}')
        if actions == -1:
            return -1
        self.player[action] = actions
        return actions

    def get_player_settings(self):
        if not self.player:
            return
        return [i['name']() for i in self._dialogsettings]

    def run(self):
        """
        Returns player after configuring
        """
        x = Dialog().select(self.filename, self.get_player_settings())
        if x == -1:
            return self.player
        try:
            value = self._dialogsettings[x]['func']()
            if self._dialogsettings[x].get('returns'):
                return value
        except IndexError:
            pass
        return self.run()
