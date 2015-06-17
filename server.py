from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests
import os

listenAddr = "128.199.82.190"
listenPort = 7654
secretKey = ""  # TODO:implement the secure feature of GitHub web hook (verify SHA1 signature)
pagureToken = "token L984SSW08QBFVEHF5IXVVWT9HNQJTX8HNSUM2XL6ECV7KUFKD7HHCYROIG0ZGGEJ"
# TODO: this is a test propose token
pagureRepo = "docs-test"
local_repo_path = '/root/doc-test'

githubToken = "token "
githubHeader = {"Authorization": githubToken}
githubUsername = "kunaaljain"
githubRepo = "centos-docs"

# TODO: now can't handle special character (Pagure don't support), should auto delete special characters

class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global pagureToken
        global pagureRepo
        self.send_response(200)
        self.end_headers()
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        if self.headers['X-Github-Event'] == 'pull_request':
            data = json.loads(post_body)

            # new PR opened
            if data['action'] == 'opened':
                print("New Pull Request opened")
                info = {'title': data['pull_request']['title'], 'creator': data['pull_request']['user']['login'],
                        'id': data['pull_request']['number'], 'link': data['pull_request']['html_url'],
                        'content': data['pull_request']['body']}
                pagure_title = "#{} {} by {}".format(str(info['id']), info['title'], info['creator'])
                # TODO: now containing all the metadata in the title, should use a more elegant solution
                if not info['content']:
                    info['content'] = "*No description provided.*"
                PR_id = str(info['id'])
                r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}/files".format(githubUsername, githubRepo, PR_id), headers=githubHeader)
                data = json.loads(r.text)
                filelist = ''
                for i in data:
                    filelist += "###{}\n\n".format(i['filename'])

                PR_HTML_Link = "https://github.com/{}/{}/pull/{}".format(githubUsername, githubRepo, PR_id)

                pagure_content = "##Files Modified\n\n{}\n\n##PR Github Link : {}\n\n##Creator : {}\n\n##Description\n\n{}\n\n".format(filelist,PR_HTML_Link,info['creator'],info['content'])
                pagure_payload = {'title': pagure_title, 'issue_content': pagure_content}
                pagure_URL = "https://pagure.io/api/0/" + pagureRepo + "/new_issue"
                pagure_head = {"Authorization": pagureToken}
                r = requests.post(pagure_URL, data=pagure_payload, headers=pagure_head)
                print(r.text)

            elif data['action'] == 'closed':
                if not data['pull_request']['merged']:
                    # TODO: insufficient pagure API
                    print("Pull request deleted without being merged")

                else:
                    # TODO: is there a more elegant way to do this?
                    print("Changes merged")
                    command = "cd " + local_repo_path + """
                    git pull origin master
                    git push pagure master
                    """
                    os.system(command)




myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Syncing tool prototype")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))