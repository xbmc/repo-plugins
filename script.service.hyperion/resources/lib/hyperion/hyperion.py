"""
    Kodi video capturer for Hyperion

	Copyright (c) 2013-2016 Hyperion Team

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in
	all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
	THE SOFTWARE.
"""
import socket
import struct

from .message_pb2 import HyperionRequest
from .message_pb2 import HyperionReply
from .message_pb2 import ColorRequest
from .message_pb2 import ImageRequest
from .message_pb2 import ClearRequest

class Hyperion(object):
    """
    Hyperion connection class.

    A Hyperion object will connect to the Hyperion server and provide
    easy to use functions to send requests

    Note that the function will block until a reply has been received
    from the Hyperion server (or the call has timed out)
    """
    
    def __init__(self, server: str, port: int) -> None:
        """
        Constructor

        Args:
            server: server address of Hyperion
            port: port number of Hyperion
        """
        # create a new socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(2)

        # Connect socket to the provided server
        self._socket.connect((server, port))

    def __del__(self) -> None:
        """Destructor"""
        # close the socket
        self._socket.close()

    def send_color(self, color, priority, duration = -1) -> None:
        """
        Send a static color to Hyperion

        Args:
            color: integer value with the color as 0x00RRGGBB
            priority: the priority channel to use
            duration: duration the leds should be set
        """
        request = HyperionRequest()
        request.command = HyperionRequest.COLOR
        color_request = request.Extensions[ColorRequest.colorRequest]
        color_request.rgbColor = color
        color_request.priority = priority
        color_request.duration = duration
        self._send_message(request)
        
    def send_image(self, width, height, data, priority, duration = -1) -> None:
        """
        Send an image to Hyperion

        Args:
            width: width of the image
            height: height of the image
            data: image data (byte string containing 0xRRGGBB pixel values)
            priority: the priority channel to use
            duration: duration the leds should be set
        """
        request = HyperionRequest()
        request.command = HyperionRequest.IMAGE
        image_request = request.Extensions[ImageRequest.imageRequest]
        image_request.imagewidth = width
        image_request.imageheight = height
        image_request.imagedata = bytes(data)
        image_request.priority = priority
        image_request.duration = duration
        self._send_message(request)
        
    def clear(self, priority) -> None:
        """Clear the given priority channel

        Args:
            priority: the priority channel to clear
        """
        request = HyperionRequest()
        request.command = HyperionRequest.CLEAR
        clear_request = request.Extensions[ClearRequest.clearRequest]
        clear_request.priority = priority
        self._send_message(request)
    
    def clear_all(self) -> None:
        """Clear all active priority channels."""
        request = HyperionRequest()
        request.command = HyperionRequest.CLEARALL
        self._send_message(request)
        
    def _send_message(self, message: HyperionRequest) -> None:
        """
        Send the given proto message to Hyperion.

        A RuntimeError will be raised if the reply contains an error

        Args:
            message : proto request to send
        """

        binary_request = message.SerializeToString()
        binary_size = struct.pack(">I", len(binary_request))
        self._socket.sendall(binary_size)
        self._socket.sendall(binary_request)

        # receive a reply from Hyperion
        size = struct.unpack(">I", self._socket.recv(4))[0]
        reply = HyperionReply()
        reply.ParseFromString(self._socket.recv(size))

        # check the reply
        if not reply.success:
            raise RuntimeError(f"Hyperion server error: {reply.error}")
