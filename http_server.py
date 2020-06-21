import sys

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from werkzeug.urls import url_parse

from flask import Flask


class WSGIRequestHandler(BaseHTTPRequestHandler):
    def make_environ(self):
        request_url = url_parse(self.path)

        if not request_url.scheme and request_url.netloc:
            path_info = f"/{request_url.netloc}{request_url.path}"
        else:
            path_info = request_url.path

        environ = {
            "wsgi.version": (1,0),
            "wsgi.url_scheme": "http",
            "wsgi.input": self.rfile,
            "wsgi.errors": sys.stderr,
            "wsgi.multithreaded": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "REQUEST_METHOD": self.command,
            "SCRIPT_NAME": "",
            "PATH_INFO": path_info,
            "QUERY_STRING": request_url.query,
            "REQUEST_URI": self.path,
        }

        for key, value in self.headers.items():
            key = key.upper().replace("-", "_")
            value = value.replace("\r\n", "")

            key = f"HTTP_{key}"
            environ[key] = value

        return environ

    def run_wsgi(self):
        self.environ = self.make_environ()

        def start_response(status, headers):
            try:
                code, msg = status.split(None, 1)
            except ValueError:
                code, msg = status, ""

            self.send_response((int(code)))

            for key, value in headers:
                self.send_header(key, value)
            
            self.send_header("Connection", "close")
            self.end_headers()

        try:
            response = self.server.app(self.environ, start_response)
            for data in response:
                if isinstance(data, bytes):
                    self.wfile.write(data)
                else:
                    self.wfile.write(data.encode('utf-8'))
        except Exception as err:
            print(err)        

    def handle(self):
        BaseHTTPRequestHandler.handle(self)

    def handle_one_request(self):
        self.raw_requestline = self.rfile.readline()

        if self.parse_request():
            self.run_wsgi()


class WSGIServer(HTTPServer):
    def __init__(self, port, handler, app):
        HTTPServer.__init__(self, port, handler)

        self.app = app
    

class PGIWSGI():
    def __init__(self, port, app):
        self.port = port
        self.app = app

    def run(self):
        httpd = WSGIServer(('', self.port), WSGIRequestHandler, self.app)
        print(f"Server running on port {self.port}")
        print("Development server")
        print("Do not run this in production or the whole world will burn down")
        httpd.serve_forever()

def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return ["Ola mundo!"]

app = Flask(__name__)

@app.route('/hello')
def hello():
    return "Ola Mundo do flask!"

if __name__ == "__main__":
    PGIWSGI(8000, app=app).run()