#!/usr/bin/env python

"""
status.py - HTTP response messages, one for each
            status code. May be raised as exceptions.
"""

__license__ = """
Copyright (c) 2001-2004 Mark Nottingham <mnot@pobox.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__version__ = "0.71"


lookup = {}
class Message:
    "Abstract class for an HTTP message."
    proto_version = None            # protocol version
    has_body = None                 # send a body with the message?
    
    def __init__(self, representation=None):
        if representation != None:
            self.representation = representation
        else:
            self.representation = Representation()
        self.headers = {}           # message headers

class Response(Message):
    "HTTP Response."
    status_code = None               # response status code
    status_phrase = None             # response status phrase

    def __str__(self):
        o = []
        o.append("%s %s %s" % (self.proto_version, self.status_code, self.status_phrase))
        o.append(str(self.headers))
        o.append('')
        if self.has_body and self.representation.body != None:
            o.append(self.representation.body)
        return o.join("\r\n")

        
class _statusLookup(type):
    """Populate lookup with a status_code -> object name map. My head hurts."""
    def __new__(metacls, name, bases, dict):
        cls = super(_statusLookup, metacls).__new__(metacls, name, bases, dict)
        try:
            lookup[dict['status_code']] = cls
        except:
            pass
        return cls

class Status(Response, Exception):  ### object
#    __metaclass__ = _statusLookup   ### Exceptions can't be new-style classes. Urgh.
    has_body = 1
    def __init__(self, headers={}, body=None):
        Response.__init__(self)
        self.headers.update(headers)
        self.representation.body = body
                
class Informational(Status):
    pass
    
class Continue(Informational):
    """
    The client SHOULD continue with its request. This interim
    response is used to inform the client that the initial part
    of the request has been received and has not yet been
    rejected by the server.
    """
    status_code = 100
    status_phrase = "Continue"
    has_body = 0
lookup[100] = Continue  ### can get rid of this once Exceptions can be new-style classes

class SwitchingProtocols(Informational):
    """ 
    The server understands and is willing to comply with the
    client's request, via the Upgrade message header field (section
    14.42), for a change in the application protocol being used on
    this connection.
    """
    status_code = 101
    status_phrase = "Switching Protocols"
    has_body = 0
lookup[101] = SwitchingProtocols

class Successful(Status):
    pass

class OK(Successful):
    """The request has succeeded."""
    status_code = 200
    status_phrase = "OK"
lookup[200] = OK
    
class Created(Successful):
    """
    The request has been fulfilled and resulted in a new resource 
    being created.
    """
    status_code = 201
    status_phrase = "Created"
lookup[201] = Created

class Accepted(Successful):
    """
    The request has been accepted for processing, but the
    processing has not been completed.
    """
    status_code = 202
    status_phrase = "Accepted"
lookup[202] = Accepted
    
class NonAuthoritativeInformation(Successful):
    """
    The returned metainformation in the entity-header is not
    the definitive set as available from the origin server,
    but is gathered from a local or a third-party copy.
    """
    status_code = 203
    status_phrase = "Non-Authoritative Information"
lookup[203] = NonAuthoritativeInformation
    
class NoContent(Successful):
    """
    The server has fulfilled the request but does not need to
    return an entity-body, and might want to return updated
    metainformation.
    """
    status_code = 204
    status_phrase = "No Content"
    has_body = 0
lookup[204] = NoContent
    
class ResetContent(Successful):
    """
    The server has fulfilled the request and the user agent
    SHOULD reset the document view which caused the request to
    be sent.
    """
    status_code = 205
    status_phrase = "Reset Content"
    has_body = 0
lookup[205] = ResetContent
    
class PartialContent(Successful):
    """
    The server has fulfilled the partial GET request for the 
    resource.
    """
    status_code = 206
    status_phrase = "Partial Content"
lookup[206] = PartialContent

class Redirection(Status):
    pass

class MultipleChoices(Redirection):
    """
    The requested resource corresponds to any one of a set of
    representations, each with its own specific location, and
    agent-driven negotiation information (section 12) is being
    provided so that the user (or user agent) can select a
    preferred representation and redirect its request to that
    location.
    """
    status_code = 300
    status_phrase = "Multiple Choices"
lookup[300] = MultipleChoices

class MovedPermanently(Redirection):
    """
    The requested resource has been assigned a new permanent URI
    and any future references to this resource SHOULD use one of
    the returned URIs.
    """
    status_code = 301
    status_phrase = "Moved Permanently"
lookup[301] = MovedPermanently

class Found(Redirection):
    """
    The requested resource resides temporarily under a different
    URI.
    """
    status_code = 302
    status_phrase = "Found"
lookup[302] = Found
    
class SeeOther(Redirection):
    """
    The response to the request can be found under a different
    URI and SHOULD be retrieved using a GET method on that
    resource.
    """
    status_code = 303
    status_phrase = "See Other"
lookup[303] = SeeOther
    
class NotModified(Redirection):
    """
    If the client has performed a conditional GET request and
    access is allowed, but the document has not been modified,
    the server SHOULD respond with this status code.
    """
    status_code = 304
    status_phrase = "Not Modified"
    has_body = 0
lookup[304] = NotModified
    
class UseProxy(Redirection):
    """
    The requested resource MUST be accessed through the proxy
    given by the Location field.
    """
    status_code = 305
    status_phrase = "Use Proxy"
    has_body = 0
lookup[305] = UseProxy
    
class TemporaryRedirect(Redirection):
    """
    The requested resource resides temporarily under a different
    URI.
    """
    status_code = 307    
    status_phrase = "Temporary Redirect"
lookup[307] = TemporaryRedirect

class ClientError(Status):
    pass
    
class BadRequest(ClientError):
    """
    The request could not be understood by the server due to
    malformed syntax.    
    """
    status_code = 400
    status_phrase = "Bad Request"
lookup[400] = BadRequest

class Unauthorized(ClientError):
    """The request requires user authentication."""
    status_code = 401
    status_phrase = "Unauthorized"
lookup[401] = Unauthorized
    
class PaymentRequired(ClientError):
    """This code is reserved for future use."""
    status_code = 402
    status_phrase = "Payment Required"
lookup[402] = PaymentRequired

class Forbidden(ClientError):
    """
    The server understood the request, but is refusing to 
    fulfill it.
    """
    status_code = 403
    status_phrase = "Forbidden"
lookup[403] = Forbidden
    
class NotFound(ClientError):
    """
    The server has not found anything matching the Request-URI.
    """
    status_code = 404
    status_phrase = "Not Found"
lookup[404] = NotFound

class MethodNotAllowed(ClientError):
    """
    The method specified in the Request-Line is not allowed
    for the resource identified by the Request-URI.
    """
    status_code = 405
    status_phrase = "Method Not Allowed"
lookup[405] = MethodNotAllowed
    
class NotAcceptable(ClientError):
    """
    The resource identified by the request is only capable of
    generating response entities which have content
    characteristics not acceptable according to the accept
    headers sent in the request.
    """
    status_code = 406
    status_phrase = "Not Acceptable"
lookup[406] = NotAcceptable
    
class ProxyAuthenticationRequired(ClientError):
    """
    This code is similar to 401 (Unauthorized), but
    indicates that the client must first authenticate itself
    with the proxy.
    """
    status_code = 407
    status_phrase = "Proxy Authentication Required"
lookup[407] = ProxyAuthenticationRequired
    
class RequestTimeout(ClientError):
    """
    The client did not produce a request within the time
    that the server was prepared to wait.
    """
    status_code = 408
    status_phrase = "Request Timeout"
lookup[408] = RequestTimeout        

class Conflict(ClientError):
    """
    The request could not be completed due to a conflict
    with the current state of the resource.
    """
    status_code = 409
    status_phrase = "Conflict"
lookup[409] = Conflict
    
class Gone(ClientError):
    """
    The requested resource is no longer available at the
    server and no forwarding address is known.
    """
    status_code = 410
    status_phrase = "Gone"
lookup[410] = Gone
    
class LengthRequired(ClientError):
    """
    The server refuses to accept the request without a
    defined Content-Length.
    """
    status_code = 411
    status_phrase = "Length Required"
lookup[411] = LengthRequired
    
class PreconditionFailed(ClientError):
    """
    The precondition given in one or more of the
    request-header fields evaluated to false when it was
    tested on the server.
    """
    status_code = 412    
    status_phrase = "Precondition Failed"
lookup[412] = PreconditionFailed
   
class RequestEntityTooLarge(ClientError):
    """
    The server is refusing to process a request because the
    request entity is larger than the server is willing or
    able to process.
    """
    status_code = 413
    status_phrase = "Request Entity Too Large"
lookup[413] = RequestEntityTooLarge
    
class RequestURITooLong(ClientError):
    """
    The server is refusing to service the request because
    the Request-URI is longer than the server is willing to
    interpret.
    """
    status_code = 414
    status_phrase = "Request-URI Too Long"
lookup[414] = RequestURITooLong
    
class UnsupportedMediaType(ClientError):
    """
    The server is refusing to service the request because
    the entity of the request is in a format not supported
    by the requested resource for the requested method.
    """
    status_code = 415
    status_phrase = "Unsupported Media Type"
lookup[415] = UnsupportedMediaType
    
class RequestedRangeNotSatisfiable(ClientError):
    """
    A server SHOULD return a response with this status code
    if a request included a Range request-header field
    (section 14.35) , and none of the range-specifier values
    in this field overlap the current extent of the selected
    resource, and the request did not include an If-Range
    request-header field.
    """
    status_code = 416
    status_phrase = "Requested Range Not Satisfiable"
lookup[416] = RequestedRangeNotSatisfiable
    
class ExpectationFailed(ClientError):
    """
    The expectation given in an Expect request-header field (see
    section 14.20) could not be met by this server, or, if the
    server is a proxy, the server has unambiguous evidence that
    the request could not be met by the next-hop server.
    """
    status_code = 417    
    status_phrase = "Expectation Failed"
lookup[417] = ExpectationFailed

class ServerError(Status):
    pass
    
class InternalServerError(ServerError):
    """
    The server encountered an unexpected condition which
    prevented it from fulfilling the request.
    """
    status_code = 500
    status_phrase = "Internal Server Error"
lookup[500] = InternalServerError

class NotImplemented(ServerError):
    """
    The server does not support the functionality required
    to fulfill the request.
    """
    status_code = 501
    status_phrase = "Not Implemented"
lookup[501] = NotImplemented

class BadGateway(ServerError):
    """
    The server, while acting as a gateway or proxy, received
    an invalid response from the upstream server it accessed
    in attempting to fulfill the request.
    """
    status_code = 502
    status_phrase = "Bad Gateway"
lookup[502] = BadGateway
    
class ServiceUnavailable(ServerError):
    """
    The server is currently unable to handle the request due
    to a temporary overloading or maintenance of the server.
    """
    status_code = 503
    status_phrase = "Service Unavailable"
lookup[503] = ServiceUnavailable
    
class GatewayTimeout(ServerError):
    """
    The server, while acting as a gateway or proxy, did not
    receive a timely response from the upstream server
    specified by the URI (e.g. HTTP, FTP, LDAP) or some
    other auxiliary server (e.g. DNS) it needed to access in
    attempting to complete the request.
    """
    status_code = 504
    status_phrase = "Gateway Timeout"
lookup[504] = GatewayTimeout
    
class HTTPVersionNotSupported(ServerError):
    """
    The server does not support, or refuses to support, the
    HTTP protocol version that was used in the request
    message.
    """
    status_code = 505
    status_phrase = "HTTP Version Not Supported"
lookup[505] = HTTPVersionNotSupported    
   
