#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import imaplib
import re
import socket
from email.parser import HeaderParser, Parser
from email.Header import decode_header

DEFAULT_FETCH_PARTS = '(BODY.PEEK[HEADER] FLAGS)'
DEFAULT_FETCH_ALL = '(RFC822)'
DEFAULT_SEARCH_CRITERIA = 'UNDELETED'
DEFAULT_MAILBOX_STATS = '(MESSAGES UNSEEN)'


class LoginError(Exception):
    pass


class UnknownError(Exception):
    pass


class InvalidCredentials(LoginError):
    pass


class InvalidHost(LoginError):
    pass


class XBMCMailClient(object):

    re_list_response = re.compile(r'\((.*?)\) "(.*)" (.*)')
    re_fetch_response = re.compile(r'([^ ]+) \(FLAGS \((.*?)\)')
    re_status_response = re.compile(r'.*\(MESSAGES (.+) UNSEEN (.+)\)')

    def __init__(self, username=None, password=None, host=None, use_ssl=True):
        self.log('connecting to server %s' % host)
        self.selected_mailbox = None
        self.logged_in = False
        if not username or not password:
            raise InvalidCredentials
        if not host:
            raise InvalidHost
        cls = imaplib.IMAP4_SSL if use_ssl else imaplib.IMAP4
        try:
            self.connection = cls(host)
            self.connection.login(username, password)
        except socket.error, error:
            self.log(error)
            raise InvalidHost(error)
        except cls.error, error:
            self.log(error)
            if 'credentials' in error.message.lower():
                raise InvalidCredentials(error)
            else:
                raise LoginError(error)
        self.logged_in = True
        self.username = username
        self.host = host
        self.log('connected.')

    def get_mailboxes(self, fetch_status=True):
        mailboxes = [{
            'name': self.__decode_modified_utf7(name),
            'raw_name': name,
            'has_children': 'HasChildren' in flags,
        } for flags, d, name in self._list_mailboxes()]
        if fetch_status:
            for mailbox in mailboxes:
                total, unseen = self._get_mailbox_status(mailbox['raw_name'])
                mailbox['total'] = total
                mailbox['unseen'] = unseen
        return mailboxes

    def get_emails(self, mailbox=None, limit=50, offset=0):
        email_ids = self._get_email_ids(mailbox)
        has_more = len(email_ids) > limit + offset
        email_ids = email_ids[offset:limit + offset]

        emails = [{
            'id': email_id,
            'mailbox': mailbox,
            'subject': self.__decode_header(email.get('Subject')),
            'from': self.__decode_header(email.get('From')),
            'unseen': not 'Seen' in flags,
        } for (email_id, flags), email in self._fetch_emails_by_ids(email_ids)]
        emails.reverse()
        return emails, has_more

    def get_email(self, email_id, mailbox=None):
        if mailbox and mailbox != self.selected_mailbox:
            self._select_mailbox(mailbox)
        if not self.selected_mailbox:
            raise ValueError('No Mailbox selected')
        self.log('fetch %s' % email_id)
        ret, data = self.connection.fetch(email_id, DEFAULT_FETCH_ALL)
        self.log(ret)
        data = [d for d in data if isinstance(d, tuple)][0]
        parser = Parser()
        parsed_email = parser.parsestr(data[1])
        body_text = ''
        for part in parsed_email.walk():
            if part.get_content_type() == 'text/plain':
                body_text += self.__decode_header(part.get_payload(decode=True))
        email = {
            'id': email_id,
            'mailbox': mailbox,
            'subject': self.__decode_header(parsed_email.get('Subject')),
            'from': self.__decode_header(parsed_email.get('From')),
            'to': self.__decode_header(parsed_email.get('To')),
            'date': self.__decode_header(parsed_email.get('Date')),
            'body_text': body_text,
        }
        return email

    def email_mark_seen(self, mail_id, mailbox=None):
        if mailbox and mailbox != self.selected_mailbox:
            self._select_mailbox(mailbox)
        if not self.selected_mailbox:
            raise ValueError('No Mailbox selected')
        self.log('store +SEEN')
        ret, data = self.connection.store(mail_id, '+FLAGS', '(\\Seen)')
        self.log(ret)

    def email_mark_unseen(self, mail_id, mailbox=None):
        if mailbox and mailbox != self.selected_mailbox:
            self._select_mailbox(mailbox)
        if not self.selected_mailbox:
            raise ValueError('No Mailbox selected')
        self.log('store -SEEN')
        ret, data = self.connection.store(mail_id, '-FLAGS', '(\\Seen)')
        self.log(ret)

    def email_delete(self, mail_id, mailbox=None):
        if mailbox and mailbox != self.selected_mailbox:
            self._select_mailbox(mailbox)
        if not self.selected_mailbox:
            raise ValueError('No Mailbox selected')
        self.log('store +DELETE')
        ret, data = self.connection.store(mail_id, '+FLAGS', '(\\Deleted)')
        self.log(ret)
        self.log('expunge')
        typ, response = self.connection.expunge()
        self.log(ret)

    def log(self, text):
        print u'[%s]: %s' % (self.__class__.__name__, repr(text))

    def logout(self):
        if self.logged_in:
            self.log('Logging out...')
            if self.selected_mailbox:
                self.connection.close()
                self.log('Mailbox deselected.')
            self.connection.logout()
            self.log('Logged out.')

    def _list_mailboxes(self):
        self.log('list')
        ret, data = self.connection.list()
        self.log(ret)
        return (self.__parse_list_response(line) for line in data)

    def _select_mailbox(self, mailbox):
        self.log('select %s' % mailbox)
        ret, data = self.connection.select(mailbox)
        self.log(ret)
        self.selected_mailbox = mailbox
        return int(data[0])

    def _get_email_ids(self, mailbox=None):
        if mailbox and mailbox != self.selected_mailbox:
            self._select_mailbox(mailbox)
        if not self.selected_mailbox:
            raise ValueError('No Mailbox selected')
        self.log('search %s' % DEFAULT_SEARCH_CRITERIA)
        ret, data = self.connection.search(None, DEFAULT_SEARCH_CRITERIA)
        self.log(ret)
        email_ids = data[0].split()
        email_ids.reverse()
        return email_ids

    def _fetch_emails_by_ids(self, email_ids, mailbox=None):
        if mailbox and mailbox != self.selected_mailbox:
            self._select_mailbox(mailbox)
        if not self.selected_mailbox:
            raise ValueError('No Mailbox selected')
        if isinstance(email_ids, (list, tuple)):
            email_ids = ','.join(email_ids)
        self.log('fetch %s' % email_ids)
        ret, data = self.connection.fetch(email_ids, DEFAULT_FETCH_PARTS)
        self.log(ret)
        data = (d for d in data if isinstance(d, tuple))
        parser = HeaderParser()
        data = (
            (self.__parse_fetch_response(status), parser.parsestr(header))
            for status, header in data
        )
        return data

    def _get_mailbox_status(self, mailbox):
        self.log('status %s' % mailbox)
        ret, data = self.connection.status(mailbox, DEFAULT_MAILBOX_STATS)
        self.log(ret)
        total, unseen = self.__parse_status_response(data[0])
        return total, unseen

    def __parse_list_response(self, line):
        flags, delimiter, name = self.re_list_response.match(line).groups()
        name = name.strip('"')
        return flags, delimiter, name

    def __parse_fetch_response(self, line):
        email_id, flags_str = self.re_fetch_response.match(line).groups()
        return email_id, flags_str

    def __parse_status_response(self, line):
        try:
            total, unseen = self.re_status_response.match(line).groups()
        except AttributeError:
            return 0, 0
        return total, unseen

    def __decode_header(self, line):
        if line:
            return decode_header(line)[0][0]
        return 'FIXME'

    def __decode_modified_utf7(self, s):

        def modified_deutf7(s):
            s_utf7 = '+' + s.replace(',', '/') + '-'
            return s_utf7.encode('latin-1').decode('utf-7')

        r = []
        _in = []
        for c in s.decode('latin-1'):
            if c == '&' and not _in:
                _in.append('&')
            elif c == '-' and _in:
                if len(_in) == 1:
                    r.append('&')
                else:
                    r.append(modified_deutf7(''.join(_in[1:])))
                _in = []
            elif _in:
                _in.append(c)
            else:
                r.append(c)
        if _in:
            r.append(modified_deutf7(''.join(_in[1:])))

        return ''.join(r)

    def __del__(self):
        self.logout()
