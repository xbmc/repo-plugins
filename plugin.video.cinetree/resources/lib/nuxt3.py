# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt.
# ------------------------------------------------------------------------------
import json
import logging

from codequick.support import logger_id
from .errors import ParseError


logger = logging.getLogger('.'.join((logger_id, __name__)))


def parse(doc):
    try:
        data = json.loads(doc)
        data_iter = iter(data)
        elem = next(data_iter)
        idx = 0
        data_idx = elem['data']
        while idx < data_idx:
            elem = next(data_iter)
            idx += 1
        root = data[elem[1]]

        for elem in data_iter:
            if isinstance(elem, dict):
                for k, v in list(elem.items()):
                    elem[k] = data[v]
            elif isinstance(elem, list):
                new_list = [data[v] for v in elem]
                elem.clear()
                elem.extend(new_list)
        return root
    except Exception:
        logger.error("Failed to parse NUXT JSON", exc_info=True)
        raise ParseError("Error parsing NUXT JSON.")
