# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------
import sys
import time
import os
import json
import logging

from codequick.support import logger_id

from . import utils
from . import fetch
from . import kodi_utils
from .errors import *


logger = logging.getLogger(logger_id + '.account')
SESS_DATA_VERS = 2


class ItvSession:
    def __init__(self):
        self._user_id = ''
        self._user_nickname = ''
        self._expire_time = 0
        self.account_data = {}
        self.read_account_data()

    @property
    def access_token(self):
        """Return the cached access token, but refresh first if it has expired.
        Raise AuthenticationError when the token is not present.

        """
        try:
            return self.account_data['itv_session']['access_token']
        except (KeyError, TypeError):
            logger.debug("Cannot produce access token from account data: %s.", self.account_data)
            return ''

    @property
    def cookie(self):
        """Return a dict containing the cookie required for authentication"""
        try:
            return self.account_data['cookies']
        except (KeyError, TypeError):
            logger.debug("Cannot produce cookies from account data: %s.", self.account_data)
            return {}

    @property
    def user_id(self):
        return self._user_id or ''

    @property
    def user_nickname(self):
        return self._user_nickname or ''

    def read_account_data(self):
        session_file = os.path.join(utils.addon_info.profile, "itv_session")
        logger.debug("Reading account data from file: %s", session_file)
        try:
            with open(session_file, 'r') as f:
                acc_data = json.load(f)
        except (OSError, IOError, ValueError) as err:
            logger.error("Failed to read account data: %r" % err)
            self.account_data = {}
            return

        if acc_data.get('vers') != SESS_DATA_VERS:
            logger.info("Converting account data from version '%s' to version '%s'",
                        acc_data.get('vers'), SESS_DATA_VERS)
            self.account_data = convert_session_data(acc_data)
            self.save_account_data()
        else:
            self.account_data = acc_data
        access_token = self.account_data.get('itv_session', {}).get('access_token')
        self._user_id, self._user_nickname, self._expire_time = parse_token(access_token)

    def save_account_data(self):
        session_file = os.path.join(utils.addon_info.profile, "itv_session")
        data_str = json.dumps(self.account_data)
        with open(session_file, 'w') as f:
            f.write(data_str)
        logger.info("ITV account data saved to file.")

    def login(self, uname: str, passw: str):
        """Sign in to itv account with `uname` and `passw`.

        Returns True on success, raises exception on failure.
        Raises AuthenticationError if login fails, or other exceptions as they occur, like e.g. FetchError.
        """
        self.account_data = {}

        req_data = {
            'grant_type': 'password',
            'nonce': utils.random_string(20),
            'username': uname,
            'password': passw,
            'scope': 'content'
        }

        logger.info("Trying to sign in to ITV account")
        try:
            # Post credentials
            session_data = fetch.post_json(
                'https://auth.prd.user.itv.com/auth',
                req_data,
                headers={'Accept': 'application/vnd.user.auth.v2+json',
                         'Akamai-BM-Telemetry': 'a=&&&e=QzNGMDA0RjYzRDkxQ0IxOTgzOTg1NTYzNURDMkJEMjl+WUFBUU5NWWN1S2p0cHl1TEFRQUFJcUNhTkJXaWlSczVGWHRaWUtKRWdCd0VyWDI0L0ZiY051QkZwYUwyWTZldUxkWVQxYTNJSnRtQWxnQkh3UTA1MGt0cWVkR2t4YTVlbzZhZ2VhN1h0QjVTQXZDOE5CYkZsa3Y3cXJZbzB1WGJXbXd3cFlSQkZDeUNTUVZGNWRpTXQwc1RCWm84UGxGVEEvTVF5ZHlJemlob0NuSXpJMFpHRkVjVVJWNndockRLL0xnRzJLZ2poYVdiNDBTYitROW5oRjd3S2JoZW13eEVOazBnWFVJd2ZiRGNYSXNGbG5IUFZZWWswQUl6WWw4SHZ6d0xZaE45V1g3QmlTSnlBcDl3blhFVzVOSm5lbWNBemdYcVlhZzdwRDQ9fjM2ODc3NDV+MzQyMDcyMw==&&&sensor_data=MjszNjg3NzQ1OzM0MjA3MjM7NTEsMSwwLDMsNywxNDQ7QGN0ITU8JU5YUkd8akZqZ1lLZ2NlZXFbISBYQktfQTBSYzY1WWNmNVNeYnEyVCV3PTlYKjdgWmAtZFlUOH5Lazp+dX5keWxebzdqaXNfI2tMU2VhPFReNzlRTVFVeTRXcHFkcnxhay5vW204Q3JDQHI0YEt1RkVdIX5MKypOeEV1Q3U5YFVhOyEjQ3Yye3EudVk9KUVKWmBEfSZkZXtebTJhUG9HRnc9Sn4zb0Q5fDhzQE07ejY6T2RASGJ+Rn1FWUgrWzNac1Q4WXBMe3ZLcCMsXWI1fU1lV1BXbjRoUSN0WCxdNT1gQT1feFA4KTFSP1E/YkYgQlNONWNnSyVkRWtRO3VxLT5GLVRxXT1FMTMlOC8lc2B4RDsuVHZSI3ZVUSwxXj9heH1zPm1YOEUoZSkgPlRDLU1yeWtBWF9RNDw/b3ZsdD54NkskQj1BPkp2PyQleVFMZX5JQ3o9LGdkU1dJSCl9Q2ptUCxZfm8kdy9DV2dpaFImZHN2VSFtX11QR01PNyheIyw/elREN1VbeiVRV3RqaDwlOUJrQDYkNCs6MTckKFsmO0VQQzJpMz9hZDpHY2NkUiRASy1tbl1jVndtJG9tZSs3TkB7JTVNZjI7LmJtTlVJMkhURnV0ciEkTUlkWloxJkFRQDVFPmxyTmlLXiEvOip4P0w9MDQjO0lkciUvLXJfdkM6KDw/djVqNmghU2p2YVs8RTImLSxFUCg1TEtkTTlpMiF2MUZ+NXk+KD1zLUc4MGAudGxzfU1jNkdxdCBxXzxaZVl3MmcweEMlWzNPXWFiLVplSH5+QmMwT2p2QS8xXSYzNU5uSyBJeTcvaSYkTS4tXy5XQjI0U31qcCwgRn14fS88LSM1Yl0tK1o9ZzQsQUdNJiUjXjpZOy4xdm1AISNmdixMc14yPXRlRSRWMDRTJW5veExjPGNGY1BoMENGL2d4OWI4KltnQkl3dEJ1KEF9aCgoVXhfMiQ7KE18NkYzb302e1M+Myh1altDKGF7On51KShpMnxSP2pJWDgxUElbIDZsWEg2RTo1LitVOVp3ZV13JGUufFdQJHc+KjdgVE5uL3BCUUFKRE89R31sJVdTP2N7VWwpc10+LGRAXzIgejsgXTs9M0xHUF5QOTdSICEgSVlCendfZUYwdl12TlFPdkE8eTAsSENVTl9JQ2JGPkB0PCZWYUZNNzYgYTVnZ2c+bWVfcWEkI1NJWmBFIFZZaTVhVTtANzsoLnheN3B6K1o0KyY7OV90MzZfSUwhZWMwM05xYXxud2Z9VlIwZH0gY0VFQlpkNjlyckMyN3ZhZCBoMjUyNy08Qk9POndhZyRkTU1ZeiZXc0BPcWojakhlMWpKPjFKRnJkOn1sWjNuc11PV2YoRWkzWXRJSF1FNVBsb0BHP15XdypFRUgzcT5ZVjJpXnk+LTh7QGd4PHpvJFBHKT0/XmkqOWBZcUtMYjgwfDtKITY+JlBMfChTRENvOSRzfixEYys8d3grcXJAZWFIcjBtM3A7LUktQ2FVUG0zM0xkYT5KfUJ0czJ+IE56eXdHWE9xaSxuTSo+bW52VyF3dC5FeSxuK2NmfiwrbEJASWsqb0Q2bl80ezxob3NSKzE0XnNQW05wQlt+cSVYR01QfEo4d1lBPW1lK1ZodGNDRE5pIWcseTV4NFVsal8+SmVFZl08MnJoRTZrOlpoVT9GR3s7JFc4bEN5P0xfRzhGZUBhZT9ALjF3a0EqNlY7aHQjLEEtY0ombUN2dysqazBBO2FgSU1GVi8haE1hLnFrIzhtRU5IJjQlUTFIZGJLbjdzTVA5Vkg4blErbjdOSkldIV1CJmVWQjdaSW8yfXE/bUw7SjZHQ1dATC8sRXZ0ejVfRXZlWEsyL2teb0U9QmA1KHUlIzg/TEVNPCBaLCwpVnd1VFkxPCV5X0NrR09OKFNNWDRtaHYzOzowJlUtQU4oQzd4e2p1P2tOTW9PKWQ1cjRZcXs4VGhDNHt+YWt2KGFdIzhJPFJDSC8sWzN1M2g+dnJhPDdBQURoZ3JIL2lOUTZVUFRQbV9ra21HfjE9KGBwaDpHdzVrcDUwN3RlI0h7TlpfbGMjJTczOmlScC58WHB0NmxmZHUuYFtzWUdXJGhNTkhucyk8TEZVOiBEYExBXWE3TC8/ezJpfDpydz1RUTI7OVZsLTtZUmJOSG0uJXc3PXA1djwoQ3UwQTUyaC0hXS4gQy5hYyo/dmlUfkdPRVslXnhfMXZFeTZVS0d4PTs0RVN6LD5mWGBne2I1e2xdJEQxUjJwYTdxK1ZLRCxZZFJrIF5uTl9PKSxVXUB+IHc9akp4aUpCbF9mNzhOMnBnaSVFeD51QGlscnordmsgJlR2Xjo8d2tQJk8wNT95W2VlL1EzWkRhSFkpLD90W3cgWCx0TUYsNnNYLF9+fmZNYGJEZjxvTyBdd3Boal1EW3tHe29SVD5OKHZIRD9TRztTYDpLPnFhKiA/LmdfJXYzWSxtY1NTVVg0LWdaay19Yis9JEspIVg7KVkxTGJRSml+b01OPFNGTzpHIGF6RkdCVXtLKW9YTTQrUTVaendwNVJDJi9+OzBHOEIteENjVVcySChfT1E6cW5OTT1NfSNHcGheYFlqIS95LWxyLm1xbTlxSC8od3JkaDwgTSkpO2U7KCMoLUBNYWV6bWM0anFqT3BmR1Q7TSo3fHExb28gYig7Izo/ZWs1P15FQ31Va29LfHhiXlZ5ZW5QRCBaW3BgLTYxR0gjKzNBTSwoWTpZYEQmcmdnaSYmKSApUjlHTzsgKzFJYzJAdnRJRFQ4di1EKXBia2wkLyRSOUUjWH4sIGBpfUBXLkIgMlhmdFtDaiV2TlpIbXE2PFRHYTR2Ql5QRV1YMEN5R305dXU4aWYwVEIrJTRNUiUlY1BXUzZWe31tfDNnMGEzYjZadzcvK0dncktbZzY5ZHs8RVBHQnI6PjdRaDNYSXpfKGFvKi4wZSZ+cSw0W21SYik2TkBJZUM9Q3MgXShuXW4kPFQrKCtbLS4lTVJ1OXoxe0xSMDJiQE5IdC95PjdzWzkoO1ptekcqNSxUXTh+IHwmTGxud1k4Pjx4P2o8N2MvSDNedFM7eWdXOlNuR25YZ0FYeExRM3oqOXUhbUw4SndKRnVMIzp1YGwkRGdCcGUwbDRoZyNrSG5rTCB7ZWNJQiZ0WzxRZkE6Slk5Uj9sXyl3Qnh9Qyx5MlU5aWRPUTVDKDRXSlcjeGElPHc7fm5XMHA/JkBUVEFYeWI/YmlYLjokJXFZcTUvIT9kQnNqSTwyUV50OlpdUHxIMWUlRThsKSYmaVFpQ0s2ZS5oQDp3bltUfXUuWFdgLUtPMC8pUEtiW3RCSG46OUB3QC5lZTs/LSlqZCZXRFspcU86XVhidjUvRzQpYC9FP3Jeay9kYWxWYT41VDE5PXxPdC0lXzpseVBvXmk7bCkxajIxeCRlenMka3JAanMqZURSO2d0MTtpdzYlMW1RaWZfKyVle3stMz8kK1k2R19ALjUtX2U7RXZ7R0haOnw4VjVyaWJwczc9STIwfF10LyhedGo4UUNAc08tfGJLMll0a0dORlhlJTNCO0EpcENMSzVDTyM8azJpLF1vcGBHLntGant4QT1ubjhARyx6R2dlTGZ+SWtGa0xrPlp3a1R9SEs3QURsIUxUeyU/KndfVzRiJUF0Q31KOVkwSGRYZy9gR0Rgai9KbjNMZHl6cTdwemU7UnxRPG5dLm8sT0lJelNVUWZzUVszWCU/ZVNILWlgZzVOPXZgKCZTOE97MCpoQEVBYndgel51SmkpNTVeRVRPNFk1fF9HN3ZaKFJfaVQjOTZaIVV9YixbfT46PnUhMDQuPyRKZUhSe25BcCVCKHF0ej4jIT5UQW0oXWx3ZFBdclF6fFdmRzkrb1J9QVpCNDdYIUY6ZCslbmJpez91QmBOe1gvdkZjPiNUIWsvbmFOY1dTTm9QOkQ3YjhKQF9XQjd8JSp7SXp8PW4gZ35HPmkkOiVHQX18XUMgUnIzJDFSemZOQT9ORVROWToxUnhxajdKOnFeRURAfFdDXzIyMFp+alVaXWpnLSU/eW8+bF1rOWdFeS1lYlNENno/ZHlvWChzYGxqIyxJUGNVT3tFU2gsVEd+M3godXNVWHdKU08zaGVhcno5SWxveiFuTCg9TnNJOnssIzR+RCBuRHkqLH1WVkZudz1JcXw0NjpwUGhtWS0odn15KyY5MCZUPUVoTTIsKE16Mz4qJDk+Syl2L0UtYWJMJENNIDEwOGJSXzNxVWRsM0YhOFUkSkVLQn5MVkQtPzU+R2x5JXopbGB4STJvKjVTdk5tS2kvQmRKNlJ4c0hPX3B5PlR5cH1kUSBDMitEXS89d0gjRHk3TzszWypqdko3PE4kJU5XYlJIeTRCL0lhPWNVcEs9LzUuM3tXeXNkdy1WajVVfjJBOjJYNzM7UXVGdmUzelZ7QVtiaUN6a153LVUkV21DSHpxYDp6IW5BZU9tYjw2bEdsOTg6c0pVYXp+XXtfJVtzMDcvb0hWYzZVPH12SENsXyRhaW9TKjs+XW9bI2swViVFT2NAeCo5aTl5eWNBNHdhOW16QHRQJFdfV0VtV3JsI15kalZBVFg5cWpKUjIsbmY0IDNFMXZSeTM4d08wcE9+TV4wY0VqKGBDMiMhb3xoZjdyI1ZELkdVPGdGIHJPOG5JWnxvZX02eFZYREhZXz9AeyAxRkY3XXxHenBHQyMkRTFNXWljLUIvbXlfenEmdXZTTnM+Njdkamg6M2llXkQpaipNS0B8PzcgJiYuK0NFTD0uRyt+KFBrfnJZI35nYUgrUDN7LmI3L28tdEBPYW1wYlcuZmFmP2RhPC0xNXwtZVRyV1VfQn12bCQgS054IS17e009ST4xWUAoJiowKDYgdjpdeTxjdGROfSFOckBTSldtRTJJJl5BJHgsUz1MSCZRZS87IHE0WjwtdlosYm1rVDJRbndSNnhneVs5RSolNU96R09PWU1VcFdoZk8hVkJGeXs+PCFwZHFBZ2VDJjBvNE1NJF9jSnltJTJlfEF4LTU8VF9xfmdZSkhzKzN7flozQUNDRGQ4K1JhNnNRS3NyaT1oPilnbTp3QXMmTTJ2WVtBLFg9eiM6YHphKlFAViFzbFhvUyk/ak5PP0goNnZaNSBnV34peSMqbyhAfGZjIzVPTl17KT98a3BlUF9HV1s1Jkx+YllrUitPRCR5PGErVVFUQzV9a3d3ezNqeD9uOzVyazFyWX5OZDxUQlNTSHh+VD18Lj5XRDNZVCk4aU8md2BJb1ElSkM0bmRTdUQoLm5+RFZqW0R7OXNWV0JtRnB0fjNaIVImPWYkVD1zN35LNFVeKiU8TS9KUDhPUytSPl07KSxCUmRJdUx4XWZwNEtYbXQjdXdDXyYuRHIyLkNtMlBseUs7fis1RTlbNWV8eFpERXZqU3UwZEk6Z2NMPG5DfS98bDpVUS44Ljg4NTNBb244W1RRbzl+UUIvJSBmMXJBaXBlLk5HJTAtTEJWUF5DOW43Ny9ZJG5WQzI5JmtfOGIwLTNzOjB+MiA6RmZdcmVfNWVgaTl7N1g0KC98LmRZJE5NY0Rqbm1ycTY/amt6e3ZJIyg3cEE7eSF0I2skY2MzX2t2Zj0/P1FgICZfYCV6JmM1QFc9YF1XUmBuYnxVVThseUB+YWlkKilibjpUcGx5VTtjbVUtJiYwMkNHTUlFNH4pUi9tcC5UZTNEdDBUV2taQGJ7VzU9QFBxUUIyMi12XndAJnU4K2J3T3NDcjc0U0gtS3ZaQk5IZX5DRGBbck1HdTUwcyxBazRwP2UqXyE3dXYzZVY+Tl8mLVFpJSg6JXxQeHloLTRqN3tDJVB4N1RKT3VWQDpHTXwwVno5Sm5TT3ZQS1lsMVs2ekY5YkhTfG9zQSh9IT9JaSZXbk9aIXBpRXEpJU9rSiVmPSxlSmIxKz14RklIaitUflN5Ul8sdSBaPEtXfkB6Y0ctKGlObTtNUzRqd3g+WS1aPF5AZXgtJW9OY255ZVIzK01sSzptQHNpdy82ZXQmNzBNRFJKJHtbcWR1XmtaUjRmWCFhKHsySF5AY0h1fW8pL3hJNmJmOFVlXm8sc0I2dilpeWlhM3E9TTotQU4vUk59aD08WDpIZE1EdipqQ0o2NkA/MSRiTmwzLHozTylkUzgsY1AtViNAPC5PcmI8UD0/eCpXTyQmRmdlVS9DIV5WPDlwZkYhQ2hzZzlVSz5CNEpDUlddTTR4PTg2W1lDKFQuKX59WzRgK0BBdTwrdiQoRU9gV3BWWXdTW2Q1YUgpKHh8cXBWQnA+TFM1aFZCWWMwO0tQaV1qL2hxfWc4fmRlZmBaY1BKel1WaDsgLXhEPmhvNUpiWFNAezU2a0dFNDE7R05HODxmUm55XzFCOmVpM0ZyKjpKTChyL0l6W2FRaFZ6dCl9fV5HZWtNQj5HaCxML3x9fCAuLHF6QDVoYWZreTtEXlhRO3lCY1UyS0olNXc8c3hNXnNqUXgsc15qaXw0V1dvfCB0ai1EOig7TnpAIEMuRHB1QygrUiFmUmRtNUdmcjMzQjouV3IgbS87bkAgVyxRJFtbUEkjRUMvT1khPGh0PEdkTUp3SlhGay1aMXZHKVk7WHFrck18eGguNWV3Um5JSWVgcThtcG87WTRqVTwtWy9Le3MrWTxBMGFySWM+YTBJZ2RvUCEqOFl9dTlFdm1CfU9yeDVjUElSJDprQ3hBc1QjcnZjQShTXyhxSE9+Jl5LdnZicHtJY2dVPV9ZQWtVd0dNUjokM0spUUsrJn5yVUZ5U211YltnbE5lTXNqMyBAeTs8L3AsSS1nV0Q8NEEod1ktSm1MQFA0JDZWOndZQXBJWSZ1a3o/fU1VRlVMWUFJeFZ3S0AuQ1owbVtJO2ZoMmYtSTUxUiN1TEo6T0ZjT1Y9c0lsbF0kRTJbTTw9JG87e0F1a2kzWEhJQStHRlVWY0cvWiMzLWZScXslT1RdfGFbSyoueltJNH5Cc1daZ0hiLyB0QWksSD80b3tveV1dQS1aITNUbjo6LURAI1pXO1BDPHRGbj1iXWFDRz5NQUEue1MrLEd6XWVWZXAtRGQjOS4zblBaYk5ydlZyZiB3IWdiPHsyOCNba1cqO2N6Qlt1bXRlPV9rTyAkcC4kOTxPQEt+UiE4e19raTY7fTNddkFGT3wpQGk3dCZ2NjlVWHlqZGQ3U3BeUWJwME55SHo6aXV1OTp+VUJhdW82PmpnKXpUWCwsRz0vSlomQTFTe0RxJTslJlV1cE5lWzEzV3AuNklRNEh4IXFXdG8ySm8jfiA8Tn1OQkZmKk1PcS9Wc2FGfXlJeUVEQVR1RXU2bEhLIW9gXzcwW2tbTihGZ21dMGtQdk9URVllfEZ7R1tVJSoydChUfns/dHE5VSpCajdtLEM+TSF1bWM7aUoraU4+NzVLSF9sRSEzJlNmPGlPeERqLDU5cldjfEVrUDY2eWxIOV4tS1ZSWlIpXXtXI21DITltbilsVmd4S3RqZyxWKzRLYmd+NH15fjVZJHNDI085YC9JY0szR2JBeHNfW0JEKntiO1ltWEtodVoka0MkaE8gU2oldWgsUjJhU0ZYRFVDOihgfEU0Kl5pM25aVnAtVTFlK0BBQ1lzYXp5QXpFJUd1KntpaGJbIG0pU31dKWo2PnY4M1UzVlhwKSFPMTZ5P0FmJUh+e1F2an4xUURsWSEwd0Rjbj09dlhEX059cyguMSQoS3ohQThHbmdePV82K3JoR2Nnc0R+dl1vfTxEbG85SSQgY19rYlZWNG1rKWRocV83K2M1bDYsMHp6PGgyP2VXXT1mLDB8RjMuMixENUIkJWVIYGlHICEmSlp5LGJkMHw2c0trIG09UGVdN2pVY1ZNR1NSRCpsfXxHX3tRcClSVGdKLEhhRygkJjxIXWt0cHNiRF15YFBpcDxTQyVOIyBqLWleI0g1c296MzlmbSMwQnhke085MU1gKD51RHdDbCo0QVdqZ2FEV2IkLVlgJS1vcU99dWJObC9TZEtnfTt6MEMuOmJHZzV9O2BsMnFbQzU0KFUsKCFEVjRVPXpTLWF5NTY/MGdfRW51IFtRbz1QcFRpLW9sOz5YLSAuK1lqTV1FaEpRMn0gYDJyNTZvS0t2LSlgWS5bKEVxQzN1aUN3SSApMmVDTk91K14mbzN1K1BRVzQhKD1xOihMVSsxZ118U15sVD9ITX5IcUh7USpJeS09dWB7JWoteV5ZQEoseUckM1QtKSo4ZUg9WD8gV11MMUU0bzMzLk5KO2IrNG0jZVBjd1pPZnxNfV1FM2RHdVhhfm5ffjQkZmpWTElIXnRBTyo8IXtNWi4oN059aEQpZXM9Mi5Fbl80PX05PnlrfXlgQ1lAOmQqaD0ueHdTRyBhc0lGQF4rI1llYiZ4KCEha1guVlpXOkQhaGU/TjMtX0l7SFBDd0M2LSwwQU1eZWZhTixTc0ZaUT8xK3B0Y3RJPF0xNTlvTD09VkIlU2EtSz4+cE1HVSp5TS9edC1vc1JGUGFeMmRNTTxfZyk0TF94bnhXLUBKMGFWRU09T0t1LmFyVGR1Wzw8O0soc2U='
                         }
            )

            self.account_data = {
                'vers': SESS_DATA_VERS,
                'refreshed': time.time(),
                'itv_session': session_data,
                'cookies': {'Itv.Session': build_cookie(session_data)}
            }
        except FetchError as e:
            # Testing showed that itv hub can return various HTTP status codes on a failed sign in attempt.
            # Sometimes returning a json string containing the reason of failure, sometimes and HTML page.
            logger.error("Error signing in to ITV account: %r" % e)
            if isinstance(e, AuthenticationError) or (isinstance(e, HttpError) and e.code in (400, 401, 403)):
                logger.info("Sign in failed: %r", e)
                raise AuthenticationError(str(e)) from None
            else:
                raise
        else:
            logger.info("Sign in successful.")
            self._user_id, self._user_nickname, self._expire_time = parse_token(session_data.get('access_token'))
            self.save_account_data()
            return True

    def refresh(self):
        """Refresh tokens.
        Perform a get request with the current renew token in the param string. ITV hub will
        return a json formatted string containing a new access token and a new renew-token.

        """
        logger.debug("Refreshing ITV account tokens...")
        try:
            token = self.account_data['itv_session']['refresh_token']
            url = 'https://auth.prd.user.itv.com/token?grant_type=refresh_token&' \
                  'token=content_token refresh_token&refresh=' + token
            # Refresh requests require no authorization header and no cookies at all
            resp = fetch.get_json(
                url,
                headers={'Accept': 'application/vnd.user.auth.v2+json'},
                timeout=10
            )
            new_tokens = resp
            session_data = self.account_data['itv_session']
            session_data.update(new_tokens)
            sess_cookie_str = build_cookie(session_data)
            logger.debug("New Itv.Session cookie: %s" % sess_cookie_str)
            self.account_data['cookies']['Itv.Session'] = sess_cookie_str
            self.account_data['refreshed'] = time.time()
            self._user_id, self._user_nickname, self._expire_time = parse_token(session_data.get('access_token'))
            self.save_account_data()
            logger.info("Tokens refreshed.")
            return True
        except (KeyError, ValueError, FetchError) as e:
            logger.warning("Failed to refresh ITVtokens - %s: %s" % (type(e), e))
        except TypeError:
            logger.warning("Failed to refresh ITV tokens - No account data present.")
        return False

    def log_out(self):
        logger.info("Signing out to ITV account")
        self.account_data = {}
        self.save_account_data()
        self._user_id = None
        self._user_nickname = None
        return True


def parse_token(token):
    """Return user_id, user nickname and token expiration time obtained from an access token.

    Token has other fields which we currently don't parse, like:
    accountProfileIdInUse
    auth_time
    scope
    nonce
    iat
    """
    import binascii
    try:
        token_parts = token.split('.')
        # Since some padding errors have been observed with refresh tokens, add the maximum just
        # to be sure padding errors won't occur. a2b_base64 automatically removes excess padding.
        token_data = binascii.a2b_base64(token_parts[1] + '==')
        data = json.loads(token_data)
        return data['sub'], data['name'], data['exp']
    except (KeyError, AttributeError, IndexError, binascii.Error) as err:
        logger.error("Failed to parse token: '%r'", err)
        return None, None, int(time.time()) + time.timezone


def build_cookie(session_data):
    cookiestr = json.dumps({
        'sticky': True,
        'tokens': {'content': session_data}
    })
    return cookiestr


_itv_session_obj = None


def itv_session():
    global _itv_session_obj
    if _itv_session_obj is None:
        _itv_session_obj = ItvSession()
    return _itv_session_obj


def fetch_authenticated(funct, url, login=True, **kwargs):
    """Call one of the fetch function with user authentication.

    Call the specified function with authentication header and return the result.
    If the server responds with an authentication error, refresh tokens, or
    login and try once again.

    To prevent headers argument to turn up as both positional and keyword argument,
    accept keyword arguments only, apart from the callable and url.

    """
    account = itv_session()
    logger.debug("making authenticated request")

    for tries in range(2):
        try:
            access_token = account.access_token
            auth_cookies = account.cookie
            if not (access_token and auth_cookies):
                raise AuthenticationError

            try:
                if account.account_data['refreshed'] < time.time() - 4 * 3600:
                    # renew tokens periodically
                    logger.debug("Token cache time has expired.")
                    raise AuthenticationError
            except (KeyError, TypeError):
                raise AuthenticationError

            cookies = kwargs.setdefault('cookies', {})
            headers = kwargs.setdefault('headers', {})
            headers['authorization'] = 'Bearer ' + account.access_token
            cookies.update(auth_cookies)
            return funct(url=url, **kwargs)
        except AuthenticationError:
            if tries > 0:
                logger.warning("Authentication failed on second attempt")
                raise AccessRestrictedError

            logger.debug("Authentication failed on first attempt")
            if account.refresh() is False:
                if login:
                    if kodi_utils.show_msg_not_logged_in():
                        from xbmc import executebuiltin
                        executebuiltin('Addon.OpenSettings({})'.format(utils.addon_info.id))
                    sys.exit(1)
                else:
                    raise


def convert_session_data(acc_data: dict) -> dict:
    acc_data['vers'] = SESS_DATA_VERS
    sess_data = acc_data.get('itv_session', '')
    acc_data['cookies'] = {'Itv.Session': build_cookie(sess_data)}
    acc_data.pop('passw', None)
    acc_data.pop('uname', None)
    return acc_data
