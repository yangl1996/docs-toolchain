from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from urllib import parse
import json
import requests

listenAddr = "128.199.82.190"
listenPort = 7655


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        self.send_response(200)
        self.end_headers()
        print(self.headers)
        print(parse.parse_qs(post_body))
        print("======================")



myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Test Server")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))