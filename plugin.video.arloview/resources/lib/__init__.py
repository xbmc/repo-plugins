import sys

__all__ = ['PY2', 'py2_encode', 'py2_decode']

PY2 = sys.version_info[0] == 2

def py2_encode(s, encoding='utf-8'):
   """
   Encode Python 2 ``unicode`` to ``str``

   In Python 3 the string is not changed.   
   """
   if PY2 and isinstance(s, unicode):
       s = s.encode(encoding)
   return s


def py2_decode(s, encoding='utf-8'):
   """
   Decode Python 2 ``str`` to ``unicode``

   In Python 3 the string is not changed.
   """
   if PY2 and isinstance(s, str):
       s = s.decode(encoding)
   return s