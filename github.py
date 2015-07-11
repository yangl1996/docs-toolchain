from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests
import os
import hmac
import hashlib
try:
    import config
except "No such file or directory":
    import config_sample as config
    print("Please set up your config.py file. Exiting.")
    exit()

listenAddr = config.listenAddr
listenPort = config.githubPort
secretKey = config.githubSecretKey
pagureToken = config.pagureToken
pagureRepo = config.pagureRepo
localRepoPath = config.localRepoPath

githubToken = config.githubToken
githubHeader = {"Authorization": "token " + githubToken}
githubUsername = config.githubUsername
githubRepo = config.githubRepo

def handle_pull_request(post_body):
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
        for changed_file in data:
            filelist += "###{}\n\n".format(changed_file['filename'])

        PR_Comment_Link = "https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername, githubRepo, PR_id)
        github_payload = {"body" : "Please find the issue corresponding to this Pull request here: https://pagure.io/docs-test/issues"}
        r = requests.post(PR_Comment_Link, data=json.dumps(github_payload), headers=githubHeader)
        print(r.text)

        PR_HTML_Link = "https://github.com/{}/{}/pull/{}".format(githubUsername, githubRepo, PR_id)
        pagure_content = "##Files Modified\n\n{}\n\n##PR Github Link : {}\n\n##Creator : {}\n\n##Description\n\n{}\n\n".format(filelist, PR_HTML_Link, info['creator'], info['content'])
        pagure_payload = {'title': pagure_title, 'issue_content': pagure_content}
        pagure_URL = "https://pagure.io/api/0/" + pagureRepo + "/new_issue"
        pagure_head = {"Authorization": "token " + pagureToken}
        r = requests.post(pagure_URL, data=pagure_payload, headers=pagure_head)
        print(r.text)

    elif data['action'] == 'closed':
        if not data['pull_request']['merged']:
            # TODO: insufficient pagure API
            print("Pull request deleted without being merged")

        else:
            # TODO: is there a more elegant way to do this?
            print("Changes merged")
            command = "cd " + localRepoPath + """
            git pull origin master
            git push pagure master
            """
            os.system(command)

class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()

        # Validate signature
        sha_name, signature = self.headers['X-Hub-Signature'].split('=')
        if sha_name != 'sha1':
            return
        mac = hmac.new(secretKey.encode(), msg=post_body.encode(), digestmod=hashlib.sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            print("Invalid signature, ignoring this call")
            return

        # Handle post body
        if self.headers['X-Github-Event'] == 'pull_request':
            handle_pull_request(post_body)




myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Syncing tool prototype")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))
