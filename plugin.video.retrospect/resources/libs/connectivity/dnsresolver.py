# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

import socket

from backtothefuture import PY2


class DnsResolver:
    def __init__(self, server):
        self.__server = server

    def get_host(self, url):
        start = url.index("//")
        start += 2
        end = url.find("/", start)
        if end > 0:
            return url[start:end]
        else:
            return url[start:]

    def resolve_address(self, address, types=(1,)):
        s = socket.socket(type=socket.SOCK_DGRAM)
        q = self.__create_request(address)
        s.settimeout(10.0)
        s.sendto(q.encode(), (self.__server, 53))
        r = s.recvfrom(1024)
        if types is None:
            return self.__parse_response(r[0])
        else:
            return [t for t in self.__parse_response(r[0]) if t[0] in types]

    def __create_request(self, address):
        # noinspection PyListCreation
        q = []
        q.append("\x00\x01")  # sequence
        q.append("\x01\x00")  # standard request
        q.append("\x00\x01")  # questions
        q.append("\x00\x00")  # answer RRS
        q.append("\x00\x00")  # authority RRS
        q.append("\x00\x00")  # additional RRS

        address_parts = address.split(".")
        for p in address_parts:
            q.append(chr(len(p)))
            q.append(p)
        q.append("\x00")
        q.append("\x00\x01")  # Type: A
        q.append("\x00\x01")  # Class: IN
        return "".join(q)

    # noinspection PyUnusedLocal
    def __parse_response(self, response):
        results = []
        reader = DnsResolver.__ByteStringReader(response)
        reader.read_integer()  # transaction_id
        reader.read_integer()  # flags
        reader.read_integer()  # questions
        answers = reader.read_integer()
        reader.read_integer()  # authority
        reader.read_integer()  # additional
        while True:
            length = reader.read_integer(1)
            if length == 0:
                break
            reader.read_bytes(length)  # address_part
            continue
        reader.read_integer()  # dns_type
        reader.read_integer()  # direction

        for i in range(0, answers):
            reader.read_full_string()  # name
            answer_type = reader.read_integer()
            reader.read_integer()  # sdirection
            reader.read_integer(4)  # ttl
            length = reader.read_integer()
            address = []
            if answer_type == 1:
                for s in range(0, length):
                    address.append(str(reader.read_integer(1)))
                address = ".".join(address)
            elif answer_type == 5:
                address = reader.read_full_string()
            else:
                raise Exception("wrong type: %s" % (answer_type, ))

            results.append((answer_type, address))
        return results

    class __ByteStringReader:  # NOSONAR
        def __init__(self, byte_string):
            self.__byteString = byte_string
            self.__pointer = 0
            self.__resumePoint = 0

        def read_integer(self, length=2):
            val = self.read_bytes(length)
            val = self.__byte_to_int(val)
            return val

        def read_full_string(self):
            value = ""
            while True:
                length = self.read_integer(1)
                if length == 0:
                    break
                elif length == 192:  # \xC0
                    # pointer found
                    new_pointer = self.read_integer(1)
                    old_pointer = self.__pointer
                    self.__pointer = new_pointer
                    value += self.read_full_string()
                    self.__pointer = old_pointer
                    break
                value += self.read_bytes(length).decode()
                value += "."
                continue
            return value.strip('.')

        def read_bytes(self, length):
            val = self.__byteString[self.__pointer:self.__pointer + length]
            self.__pointer += length
            return val

        def __byte_to_int(self, byte_string):
            if PY2:
                return int(byte_string.encode('hex'), 16)
            # noinspection PyUnresolvedReferences
            return int.from_bytes(byte_string, byteorder='big')
