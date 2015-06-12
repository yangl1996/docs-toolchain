from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json

listenAddr = "128.199.244.33"
listenPort = 7654


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.['content-length'])
        post_body = self.rfile.read(content_len)
        data = json.loads(post_body)
        print(data)


myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Syncing tool prototype")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Picture Server Stops - %s:%s" % (listenAddr, listenPort))