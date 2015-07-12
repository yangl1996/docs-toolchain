from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests
import os
import hmac
import hashlib
import threading
try:
    import config
except "No such file or directory":
    import config_sample as config
    print("Please set up your config.py file. Exiting.")
    exit()

# import configurations from config.py
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


# handle new pull request on github
def handle_pull_request(post_body):
    data = json.loads(post_body)

    # new PR opened
    if data['action'] == 'opened':
        print("New Pull Request opened")
        info = {'title': data['pull_request']['title'], 'creator': data['pull_request']['user']['login'],
                'id': data['pull_request']['number'], 'link': data['pull_request']['html_url'],
                'content': data['pull_request']['body']}
        pagure_title = "#{} {} by {}".format(str(info['id']), info['title'], info['creator'])
        if not info['content']:
            info['content'] = "*No description provided.*"
        PR_id = str(info['id'])
        r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}/files".format(githubUsername, githubRepo, PR_id), headers=githubHeader)
        data = json.loads(r.text)
        filelist = ''
        for changed_file in data:
            filelist += "###{}\n\n".format(changed_file['filename'])

        PR_HTML_Link = "https://github.com/{}/{}/pull/{}".format(githubUsername, githubRepo, PR_id)
        pagure_content = "##Files Modified\n\n{}\n\n##PR Github Link : {}\n\n##Creator : {}\n\n##Description\n\n{}\n\n".format(filelist, PR_HTML_Link, info['creator'], info['content'])
        pagure_payload = {'title': pagure_title, 'issue_content': pagure_content}
        pagure_URL = "https://pagure.io/api/0/" + pagureRepo + "/new_issue"
        pagure_head = {"Authorization": "token " + pagureToken}
        r = requests.post(pagure_URL, data=pagure_payload, headers=pagure_head)
        print(r.text)

    # PR closed
    elif data['action'] == 'closed':
        # not merged
        if not data['pull_request']['merged']:
            # TODO: insufficient pagure API, we can directly modify the ticket repo
            print("Pull request deleted without being merged")

        # merged
        else:
            # TODO: is there a more elegant way to do this?
            print("Changes merged")
            command = "cd " + localRepoPath + """
            git pull origin master
            git push pagure master
            """
            os.system(command)


def handle_pull_request_comment(post_body):

    data = json.loads(post_body)

    # currently github are not providing comment deletion webhook
    if data['action'] == 'created':
        print("New comment created")
        info = {'issue_name': data['issue']['title'],
                'issue_id': data['issue']['number'],
                'comment': data['comment']['body'],
                'username': data['comment']['user']['login']}
        # we auto create an comment pointing to pagure when new PR is opened, should ignore this one
        if info['comment'].startswith("[Issue #"):
            return
        # no infinity loop
        if info['comment'].startswith("*Commented by"):
            return

        # prepare pagure comment body
        comment_body = """*Commented by {}*
        {}""".format(info['username'], info['comment'])

        # get pagure issue id
        r = requests.get("https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername, githubRepo, info['issue_id']),
                         headers=githubHeader)
        data = json.loads(r.text)
        info_body = data[0]['body']
        pagure_id = int(info_body[8:info_body.find(']')])
        pagure_URL = "https://pagure.io/api/0/{}/issue/{}/comment".format(pagureRepo, pagure_id)
        pagure_head = {"Authorization": "token " + pagureToken}
        pagure_payload = {"comment": comment_body}
        r = requests.post(pagure_URL, data=pagure_payload, headers=pagure_head)
        print(r.text)




# main server class
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
            th = threading.Thread(target=handle_pull_request, args=(post_body,))
            th.start()

        elif self.headers['X-Github-Event'] == 'issue_comment':
            th = threading.Thread(target=handle_pull_request_comment, args=(post_body,))
            th.start()



myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Syncing tool prototype")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))
