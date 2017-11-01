import json
import BaseHTTPServer

class OneDriveHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    file_map = {}
    
    def do_HEAD(self):
        self.do_GET()
        return
    
    def do_GET(self):
        url = ''
        if self.path in self.file_map:
            url = self.file_map[self.path]
        self.send_response(303)
        self.send_header('Location', url)
        self.end_headers()
        return
    
    def do_POST(self):
        self.file_map[self.path] = self.headers.get('download-url') 
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': 'true', self.path : self.file_map[self.path]}));
        self.wfile.close()
        