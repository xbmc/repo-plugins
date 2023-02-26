"""
    tknorris shared module

    Copyright (C) 2016 tknorris
    Copyright (C) 2016-2018 Twitch-on-Kodi

    Modified by Twitch-on-Kodi/plugin.video.twitch Dec. 12, 2016

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from . import log_utils


class URL_Dispatcher:
    def __init__(self):
        self.func_registry = {}
        self.args_registry = {}
        self.kwargs_registry = {}

    def register(self, mode, args=None, kwargs=None):
        """
        Decorator function to register a function as a plugin:// url endpoint

        mode: the mode value passed in the plugin:// url
        args: a list  of strings that are the positional arguments to expect
        kwargs: a list of strings that are the keyword arguments to expect

        * Positional argument must be in the order the function expect
        * kwargs can be in any order
        * kwargs without positional arguments are supported by passing in a kwargs but no args
        * If there are no arguments at all, just "mode" can be specified
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = []

        def decorator(f):
            if mode in self.func_registry:
                message = 'Error: %s already registered as %s' % (str(f), mode)
                log_utils.log(message, log_utils.LOGERROR)
                raise Exception(message)

            # log_utils.log('registering function: |%s|->|%s|' % (mode,str(f)), xbmc.LOGDEBUG)
            self.func_registry[mode.strip()] = f
            self.args_registry[mode] = args
            self.kwargs_registry[mode] = kwargs
            # log_utils.log('registering args: |%s|-->(%s) and {%s}' % (mode, args, kwargs), xbmc.LOGDEBUG)

            return f

        return decorator

    def dispatch(self, mode, queries):
        """
        Dispatch function to execute function registered for the provided mode

        mode: the string that the function was associated with
        queries: a dictionary of the parameters to be passed to the called function
        """
        if mode not in self.func_registry:
            message = 'Error: Attempt to invoke unregistered mode |%s|' % (mode)
            log_utils.log(message, log_utils.LOGERROR)
            raise Exception(message)

        args = []
        kwargs = {}
        unused_args = queries.copy()
        if self.args_registry[mode]:
            # positional arguments are all required
            for arg in self.args_registry[mode]:
                arg = arg.strip()
                if arg in queries:
                    args.append(self.__coerce(queries[arg]))
                    del unused_args[arg]
                else:
                    message = 'Error: mode |%s| requested argument |%s| but it was not provided.' % (mode, arg)
                    log_utils.log(message, log_utils.LOGERROR)
                    raise Exception(message)

        if self.kwargs_registry[mode]:
            # kwargs are optional
            for arg in self.kwargs_registry[mode]:
                arg = arg.strip()
                if arg in queries:
                    kwargs[arg] = self.__coerce(queries[arg])
                    del unused_args[arg]

        if 'mode' in unused_args: del unused_args['mode']  # delete mode last in case it's used by the target function
        log_utils.log('Calling |%s| for mode |%s| with pos args |%s| and kwargs |%s|' % (self.func_registry[mode].__name__, mode, args, kwargs), log_utils.LOGNOTICE)
        if unused_args: log_utils.log('Warning: Arguments |%s| were passed but unused by |%s| for mode |%s|' % (unused_args, self.func_registry[mode].__name__, mode),
                                      log_utils.LOGWARNING)
        self.func_registry[mode](*args, **kwargs)

    # since all params are passed as strings, do any conversions necessary to get good types (e.g. boolean)
    def __coerce(self, arg):
        temp = arg.lower()
        if temp == 'true':
            return True
        elif temp == 'false':
            return False
        elif temp == 'none':
            return None

        return arg
