# (c) Roman Miroshnychenko <roman1972@gmail.com> 2023
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Exception logger with extended diagnostic info"""

import inspect
import sys
from contextlib import contextmanager
from platform import uname
from pprint import pformat
from typing import Any, Dict, Callable, Generator, Iterable, Optional

import xbmc


def _log_error(message: str) -> None:
    xbmc.log(message, level=xbmc.LOGERROR)


def _format_vars(variables: Dict[str, Any]) -> str:
    """
    Format variables dictionary

    :param variables: variables dict
    :return: formatted string with sorted ``var = val`` pairs
    """
    var_list = [(var, val) for var, val in variables.items()
                if not (var.startswith('__') or var.endswith('__'))]
    var_list.sort(key=lambda i: i[0])
    lines = []
    for var, val in var_list:
        lines.append(f'{var} = {pformat(val)}')
    return '\n'.join(lines)


def _format_code_context(frame_info: inspect.FrameInfo) -> str:
    context = ''
    if frame_info.code_context is not None:
        for i, line in enumerate(frame_info.code_context, frame_info.lineno - frame_info.index):
            if i == frame_info.lineno:
                context += f'{str(i).rjust(5)}:>{line}'
            else:
                context += f'{str(i).rjust(5)}: {line}'
    return context


FRAME_INFO_TEMPLATE = """File:
{file_path}:{lineno}
----------------------------------------------------------------------------------------------------
Code context:
{code_context}
----------------------------------------------------------------------------------------------------
Local variables:
{local_vars}
====================================================================================================
"""


def _format_frame_info(frame_info: inspect.FrameInfo) -> str:
    return FRAME_INFO_TEMPLATE.format(
        file_path=frame_info.filename,
        lineno=frame_info.lineno,
        code_context=_format_code_context(frame_info),
        local_vars=_format_vars(frame_info.frame.f_locals)
    )


STACK_TRACE_TEMPLATE = """
####################################################################################################
                                            Stack Trace
====================================================================================================
{stack_trace}
************************************* End of diagnostic info ***************************************
"""


def _format_stack_trace(frames: Iterable[inspect.FrameInfo]) -> str:
    stack_trace = ''
    for frame_info in frames:
        stack_trace += _format_frame_info(frame_info)
    return STACK_TRACE_TEMPLATE.format(stack_trace=stack_trace)


EXCEPTION_TEMPLATE = """
####################################################################################################
                                     Exception Diagnostic Info
----------------------------------------------------------------------------------------------------
Exception type    : {exc_type}
Exception message : {exc}
System info       : {system_info}
Python version    : {python_version}
Kodi version      : {kodi_version}
sys.argv          : {sys_argv}
----------------------------------------------------------------------------------------------------
sys.path:
{sys_path}
{stack_trace_info}
"""


def format_trace(frames_to_exclude: int = 1) -> str:
    """
    Returns a pretty stack trace with code context and local variables

    Stack trace info includes the following:

    * File path and line number
    * Code fragment
    * Local variables

    It allows to inspect execution state at the point of this function call

    :param frames_to_exclude: How many top frames are excluded from the trace
        to skip unnecessary info. Since each function call creates a stack frame
        you need to exclude at least this function frame.
    """
    frames = inspect.stack(5)[frames_to_exclude:]
    return _format_stack_trace(reversed(frames))


def format_exception(exc_obj: Optional[Exception] = None) -> str:
    """
    Returns a pretty exception stack trace with code context and local variables

    :param exc_obj: exception object (optional)
    :raises ValueError: if no exception is being handled
    """
    if exc_obj is None:
        _, exc_obj, _ = sys.exc_info()
    if exc_obj is None:
        raise ValueError('No exception is currently being handled')
    stack_trace = inspect.getinnerframes(exc_obj.__traceback__, context=5)
    stack_trace_info = _format_stack_trace(stack_trace)
    message = EXCEPTION_TEMPLATE.format(
        exc_type=exc_obj.__class__.__name__,
        exc=exc_obj,
        system_info=uname(),
        python_version=sys.version.replace('\n', ' '),
        kodi_version=xbmc.getInfoLabel('System.BuildVersion'),
        sys_argv=pformat(sys.argv),
        sys_path=pformat(sys.path),
        stack_trace_info=stack_trace_info
    )
    return message


@contextmanager
def catch_exception(logger_func: Callable[[str], None] = _log_error) -> Generator[None, None, None]:
    """
    Diagnostic helper context manager

    It controls execution within its context and writes extended
    diagnostic info to the Kodi log if an unhandled exception
    happens within the context. The info includes the following items:

    - System info
    - Python version
    - Kodi version
    - Module path.
    - Stack trace including:
        * File path and line number where the exception happened
        * Code fragment where the exception has happened.
        * Local variables at the moment of the exception.

    After logging the diagnostic info the exception is re-raised.

    Example::

        with catch_exception():
            # Some risky code
            raise RuntimeError('Fatal error!')

    :param logger_func: logger function that accepts a single argument
        that is a log message.
    """
    try:
        yield
    except Exception as exc:
        message = format_exception(exc)
        # pylint: disable=line-too-long
        logger_func('\n*********************************** Unhandled exception detected ***********************************\n'
                    + message)
        raise
