# SPDX-License-Identifier: GPL-3.0-or-later

import io

import xbmc
import xbmcgui

from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.urihandler import UriHandler


class WebDialogue(object):
    def __init__(self, bind_interface="", port=3145):
        """ Initializes a WebDialogue object.

        :param str bind_interface:  The interface to bind the http server to.
        :param int port:            The TCP port number to bind to.

        """

        self.bind_interface = bind_interface
        self.port = port
        self.__value = None
        return

    # noinspection PyCompatibility
    def input(self, heading, text, time_out=30):
        """ Show an input dialog.

        :param str|int heading:     Dialog heading.
        :param str|int text:        Default value.
        :param int time_out:        Seconds to autoclose dialog (default=do not autoclose).

        :return: Returns the entered data as a string. Returns an empty string if dialog was canceled.
        :rtype: str

        """

        if isinstance(heading, int):
            heading = LanguageHelper.get_localized_string(heading)
        if isinstance(text, int):
            text = LanguageHelper.get_localized_string(text)

        server_address = (self.bind_interface, self.port)

        pb = xbmcgui.DialogProgress()
        pb.create(LanguageHelper.get_localized_string(30114), LanguageHelper.get_localized_string(30115))

        from http.server import HTTPServer
        from http.server import BaseHTTPRequestHandler

        # Create simple handler class
        class RetroHandler(BaseHTTPRequestHandler):
            artwork = {
                "fanart": (Config.fanart, "image/jpeg"),
                "poster": (Config.poster, "image/jpeg"),
                "icon": (Config.icon, "image/png")
            }

            cancel = xbmc.getLocalizedString(222)
            ok = xbmc.getLocalizedString(186)

            def __init__(self, request, client_address, server):
                """

                :param request:                 The request information
                :param client_address:          Tha address of the client
                :param RetroHTTPServer server:  A HTTP server instance.

                """

                # Set the handler timeout so connections from browsers get killed faster.
                self.timeout = 1
                # We need the server to be accessible.
                self.server = server        # type: RetroHTTPServer
                BaseHTTPRequestHandler.__init__(self, request, client_address, server)

            # noinspection PyPep8Naming
            def do_GET(self):
                if self.path.startswith("/image/"):
                    path, mime = RetroHandler.artwork.get(self.path.rsplit("/", 1)[-1], (None, None))
                    if not path:
                        self.send_error(404, "NOT FOUND")
                        self.__fill_and_end_headers()
                        return

                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    with io.open(path, mode='br') as fp:
                        data = fp.read()
                        self.send_header('Content-Length', str(len(data)))
                        self.__fill_and_end_headers()
                        self.wfile.write(data)
                    return

                elif self.path != "/":
                    self.send_error(404, "NOT FOUND")
                    self.__fill_and_end_headers()
                    return

                self.send_response(200)
                # noinspection PyUnresolvedReferences
                max_waiting_time = self.server.input_time_out
                # noinspection PyUnresolvedReferences
                time_remaining = self.server.input_time_remaining
                html = self.__get_html(
                    Config.appName, heading, text, max_waiting_time, time_remaining,
                    RetroHandler.ok, RetroHandler.cancel).encode("utf-8")

                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html)))
                self.__fill_and_end_headers()
                self.wfile.write(html)
                self.server.active = True
                return

            # noinspection PyPep8Naming
            def do_POST(self):
                if self.path != "/":
                    self.send_error(404, "NOT FOUND")
                    return
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = {}
                for kv in post_data.split("&"):
                    key, value = kv.split("=", 1)
                    data[key] = HtmlEntityHelper.url_decode(value)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(self.__close_html().encode("utf-8"))
                self.server._BaseServer__shutdown_request = True

                if "cancel" in data:
                    Logger.trace("RetroServer: Received a 'Cancel' POST request")
                    self.server.cancelled = True
                else:
                    Logger.trace("RetroServer: Received a 'Ok' POST request")
                    self.server.completed = True
                self.server.value = data["value"]
                return

            # noinspection PyShadowingBuiltins
            def log_message(self, format, *args):
                text = format % args
                Logger.trace("RetroServer: %s", text)

            def __fill_and_end_headers(self):
                self.send_header("Keep-Alive", "max=0")
                self.send_header('Connection', 'close')
                self.end_headers()

            def __close_html(self):
                return """<html>
                    <head>
                    <body style="background-color: black; 
                                 font-family: sans-serif;
                                 color: white">
                    </body>
                    </html>
                    """""

            def __get_html(self, title, setting_name, setting_value, max_waiting_time, time_remaining, ok="Ok", cancel="Cancel"):
                """ Creates the dialog HTML page.

                :param str title:             The title of the dialogue.
                :param str setting_name:      The label for the setting.
                :param str setting_value:     The value for the setting.
                :param int max_waiting_time:  Timeout for the input.
                :param int time_remaining:    Time remaining for the input.
                :param str ok:                Label for OK button.
                :param str cancel:            Label for Cancel button.

                :return: A valid HTML5 dialogue HTML page.
                :rtype: str

                """

                return """<!DOCTYPE html>
                    <html>
                    <head>
                    <body style="background-color: black; 
                                 background-image: url('image/fanart'); 
                                 background-position: center top;
                                 font-family: sans-serif;
                                 color: white;">
    
                    <h1>{0}</h2> 
                    <form id="webdialogue" action="/" method="post">
                      <label for="value">{1}:</label><br />
                      <fieldset id="dialogueFields" style="border-width: 0px; padding: 0">
                          <input type="text" id="value" name="value" placeholder="{2}" value="" style="margin: 10px 0px; min-width: 450px;" />
                          <br />
                          <progress value="{3}" max="{4}" id="pbar" style="margin: 10px 0px; width: 457px;" ></progress> 
                          <br />
                          <br />
                          <input type="submit" name="ok" value="{5}" />
                          <input type="submit" name="cancel" value="{6}" />
                       </fieldset>
                    </form>
                    
                    <script type="text/javascript">
                        var reverse_counter = {3};
                        var downloadTimer = setInterval(function(){{
                            reverse_counter--;
                            document.getElementById("pbar").value = reverse_counter;
                            if(reverse_counter <= 0) {{
                                clearInterval(downloadTimer);
                                document.getElementById("dialogueFields").disabled = "disabled"
                            }}
                        }},1000);
                    </script>
                    </body>
                    </html>
                    """.format(title, setting_name, setting_value, time_remaining,
                               max_waiting_time, ok, cancel)

        class RetroHTTPServer(HTTPServer, xbmc.Monitor):
            # noinspection PyPep8Naming
            def __init__(self, server_address, RequestHandlerClass, input_time_out):  # NOSONAR
                HTTPServer.__init__(self, server_address, RequestHandlerClass)
                xbmc.Monitor.__init__(self)
                self.value = None
                self.cancelled = False
                self.completed = False
                self.active = False
                self.input_time_out = input_time_out
                self.input_time_remaining = input_time_out

            def handle_error(self, request, client_address):
                """Handle an error gracefully. May be overridden.

                The default is to print a traceback and continue.

                """
                import traceback
                Logger.error("RetroServer: %s", traceback.format_exc())

            def force_stop(self):
                Logger.debug("RetroServer: Forcing a shutdown.")
                self.shutdown()
                self.socket.close()

        try:
            pb.update(1, LanguageHelper.get_localized_string(30116).format(self.port))
            httpd = RetroHTTPServer(server_address, RetroHandler, time_out)

            import threading
            th = threading.Thread(target=httpd.serve_forever)
            th.daemon = True
            th.start()

            ipaddress = xbmc.getInfoLabel("network.ipaddress")
            pb.update(2, LanguageHelper.get_localized_string(30119).format(ipaddress, self.port))

            Logger.info("RetroServer: Serving on %s", self.port)

            for i in range(0, time_out):
                if pb.iscanceled():
                    Logger.debug("RetroServer: User aborted the dialogue.")
                    break

                httpd.input_time_remaining -= 1
                percentage = 100 - int(i * 100.0/time_out)
                stop = False
                if httpd.completed:
                    Logger.debug("RetroServer: Browser input received.")
                    pb.update(percentage, LanguageHelper.get_localized_string(30118))
                    stop = True
                elif httpd.cancelled:
                    Logger.debug("RetroServer: Browser input cancelled.")
                    pb.update(percentage, LanguageHelper.get_localized_string(30120))
                    stop = True
                elif httpd.abortRequested():
                    Logger.debug("RetroServer: Kodi requested a stop.")
                    break
                elif httpd.active:
                    Logger.debug("RetroServer: Input page was presented.")
                    pb.update(percentage, LanguageHelper.get_localized_string(30117))
                else:
                    pb.update(percentage)

                # We sleep here to make sure we can read the response.
                httpd.waitForAbort(1)
                if stop:
                    Logger.trace("RetroServer: Aborting loop.")
                    break
            pb.close()

            httpd.force_stop()
            if th.is_alive():
                th.join()

            # noinspection PyUnusedLocal
            th = None  # NOSONAR
            return httpd.value, httpd.cancelled
        except:
            Logger.critical("RetroServer: Error with WebDialogue", exc_info=True)
            return None, False


if __name__ == '__main__':
    Logger.create_logger(None, "WebDialogue", min_log_level=0)
    UriHandler.create_uri_handler()
    d = WebDialogue()
    print(d.input("Cookie value for site", "test", time_out=30))
