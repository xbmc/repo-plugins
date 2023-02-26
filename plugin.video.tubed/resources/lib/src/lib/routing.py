# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""


class Router:

    def __init__(self):
        self._functions = {}
        self._args = {}
        self._kwargs = {}

    def route(self, mode, args=None, kwargs=None):
        mode = str(mode)

        if args is None:
            args = []
        if kwargs is None:
            kwargs = []

        def decorator(func):
            if mode in self._functions:
                message = '%s already registered as %s' % (str(func), mode)
                raise Exception(message)  # pylint: disable=broad-exception-raised

            self._functions[mode] = func
            self._args[mode] = args
            self._kwargs[mode] = kwargs

            return func

        return decorator

    def invoke(self, query):
        mode = query.get('mode')

        if mode not in self._functions:
            message = 'Attempted to invoke an unregistered mode %s' % mode
            raise Exception(message)  # pylint: disable=broad-exception-raised

        args = []
        kwargs = {}
        unused = query.copy()

        if self._args[mode]:
            for arg in self._args[mode]:
                arg = arg.strip()
                if arg in query:
                    args.append(self._cast(query[arg]))
                    del unused[arg]
                    continue

                message = 'Mode %s requested argument %s which was not provided.' % (mode, arg)
                raise Exception(message)  # pylint: disable=broad-exception-raised

        if self._kwargs[mode]:
            for arg in self._kwargs[mode]:
                arg = arg.strip()
                if arg in query:
                    kwargs[arg] = self._cast(query[arg])
                    del unused[arg]

        if 'mode' in unused:
            del unused['mode']

        self._functions[mode](*args, **kwargs)

    @staticmethod
    def _cast(arg):
        lowercase = arg.lower()

        if lowercase == 'true':
            return True

        if lowercase == 'false':
            return False

        if lowercase == 'none':
            return None

        return arg
