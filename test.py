from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from urllib import parse
import json
import requests

listenAddr = "128.199.82.190"
listenPort = 7655
pagureRepo = "docs-test"
temp_file_path = "temp.json"

last_issue_list = []

try:
    temp_file = open(temp_file_path, 'r')
    file_content = temp_file.read()
    last_issue_list = json.loads(file_content)['issue']
    temp_file.close()
except:
    print("No temp file found, initializing new temp file")


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global last_issue_list
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        self.send_response(200)
        self.end_headers()
        print(self.headers)
        print(parse.parse_qs(post_body))
        print("======================")
        if self.headers['X-Pagure-Topic'] == "issue.edit":
            r = requests.get("https://pagure.io/api/0/" + pagureRepo + "/issues")
            new_file = r.text
            new_json = json.loads(new_file)
            new_issue_list = new_json['issues']
            difference = last_issue_list - new_issue_list
            last_issue_list = new_issue_list
            to_write = json.dumps(new_json)
            writer = open(temp_file_path, 'w')
            writer.write(to_write)
            writer.close()
            deleted_title = difference[0]['title']
            print(deleted_title)
            print("=========END INFO=========")
            # TODO: need sync to github



myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Test Server")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))