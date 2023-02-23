# URL Dispatcher library

# SPDX-License-Identifier: GPL-3.0
# See LICENSES/GPL-3.0 for more information.

import xbmc


class URLDispatcher:

    def __init__(self):

        self.func_registry = {}
        self.args_registry = {}
        self.kwargs_registry = {}

    def register(self, action, args=None, kwargs=None):

        """
        Decorator function to register a function as a plugin:// url endpoint

        action: the action value passed in the plugin:// url
        args: a list  of strings that are the positional arguments to expect
        kwargs: a list of strings that are the keyword arguments to expect

        * Positional argument must be in the order the function expect
        * kwargs can be in any order
        * kwargs without positional arguments are supported by passing in a kwargs but no args
        * If there are no arguments at all, just "action" can be specified
        """

        if args is None:
            args = []
        if kwargs is None:
            kwargs = []

        def decorator(f):

            if action in self.func_registry:
                message = 'Error: {0} already registered as {1}'.format(str(f), action)
                raise Exception(message)

            self.func_registry[action.strip()] = f
            self.args_registry[action] = args
            self.kwargs_registry[action] = kwargs

            return f

        return decorator

    def dispatch(self, action, queries):

        """
        Dispatch function to execute function registered for the provided action

        action: the string that the function was associated with
        queries: a dictionary of the parameters to be passed to the called function
        """

        if action not in self.func_registry:
            message = 'Error: Attempt to invoke unregistered action |{0}|'.format(action)
            raise Exception(message)

        args = []
        kwargs = {}
        unused_args = queries.copy()
        if self.args_registry[action]:
            # positional arguments are all required
            for arg in self.args_registry[action]:
                arg = arg.strip()
                if arg in queries:
                    args.append(self.__coerce(queries[arg]))
                    del unused_args[arg]
                else:
                    message = 'Error: action |{0}| requested argument |{1}| but it was not provided.'.format(action, arg)
                    raise Exception(message)

        if self.kwargs_registry[action]:
            # kwargs are optional
            for arg in self.kwargs_registry[action]:
                arg = arg.strip()
                if arg in queries:
                    kwargs[arg] = self.__coerce(queries[arg])
                    del unused_args[arg]

        if 'action' in unused_args:
            del unused_args['action']  # delete action last in case it's used by the target function
        if unused_args:
            pass
        self.func_registry[action](*args, **kwargs)

    def showactions(self):

        for action in self.func_registry:

            value = self.func_registry[action]
            args = self.args_registry[action]
            kwargs = self.kwargs_registry[action]
            line = 'Action {0} Registered - {1} args: {2} kwargs: {3}'.format(
                str(action), str(value), str(args), str(kwargs)
            )
            xbmc.log(line, xbmc.LOGDEBUG)

    # since all params are passed as strings, do any conversions necessary to get good types (e.g. boolean)
    @staticmethod
    def __coerce(arg):

        try:

            temp = arg.lower()

            if temp == 'true':
                return True
            elif temp == 'false':
                return False
            elif temp == 'none':
                return None

            return arg

        except:
            return arg


urldispatcher = URLDispatcher()

__all__ = ['urldispatcher']
