from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests
import os
import hmac
import hashlib
import threading
import markdown
from urllib.request import urlopen
import libpagure
import logging
try:
    import config
except "No such file or directory":
    import config_sample as config
    logging.critical("Configuration file not found.")
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

CIserver = config.CIserver
CIrepopath = config.CIrepopath

pagure = libpagure.Pagure(pagureToken, pagureRepo)

# handle new pull request on github
def handle_pull_request(post_body):
    data = json.loads(post_body)  # parse web hook payload

    # new PR opened
    if data['action'] == 'opened':
        logging.info("New pull request opened on GitHub.")
        info = {'title': data['pull_request']['title'], 'creator': data['pull_request']['user']['login'],
                'id': data['pull_request']['number'], 'link': data['pull_request']['html_url'],
                'content': data['pull_request']['body'], 'patch_url' : data['pull_request']['patch_url']}  # get github PR info
        pagure_title = "#{} {} by {}".format(str(info['id']), info['title'], info['creator'])  # generate pagure issue title
        if not info['content']:  # empty PR description
            info['content'] = "*No description provided.*"
        PR_id = str(info['id'])  # get github PR id
        # call github api to get modified file list of the PR
        r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}/files".format(githubUsername, githubRepo, PR_id), headers=githubHeader)
        data = json.loads(r.text)  # parse api return value
        # generate a list of modified files

        patch_data = urlopen(info['patch_url'])
        patch_file = '{}.patch'.format(info['id'])
        patch_path = localRepoPath + '/' + 'localdata' + '/' + PR_id + '/'
        #create dir

        if not os.path.exists(os.path.dirname(patch_path)):
            os.makedirs(os.path.dirname(patch_path))
        
        f = open(patch_path + patch_file,'w')
        f.write(patch_data.read().decode('utf-8'))
        f.close()

        command = "cd " + localRepoPath + '\n' + "git apply {}".format('localdata' + '/' + PR_id + '/' + patch_file)
        os.system(command)

        filelist = '<code>'
        for changed_file in data:
            filelist += "{}\n".format(changed_file['filename'])
        filelist += "</code>"

        filelistname = "filelist-pr-{}.json".format(PR_id)
        filelistdata = []
        payfileadd = ' '
        
        for changed_file in data:
            #create path
            if not os.path.exists(os.path.dirname(CIrepopath + '/' + PR_id + '/' + changed_file['filename'])):
                os.makedirs(os.path.dirname(CIrepopath + '/' + PR_id + '/' + changed_file['filename']))
            
            html = markdown.markdownFromFile(input = localRepoPath + '/' + changed_file['filename'], output = CIrepopath + '/' + PR_id + '/' + changed_file['filename'].split('.')[0] +'.html', output_format="html5")
            built = True
            filename = changed_file['filename']
            filelistdata.append({'filename' : filename, 'built' : built, 'builtfile' : PR_id + '/' + changed_file['filename'].split('.')[0] + '.html'})
            payfileadd += '<tr> <th> {} </th> <td> <a href="{}.html" target="_blank">{}</a></td> </tr>'.format(filename, CIserver + PR_id + '/' + changed_file['filename'].split('.')[0],filename)

        # print(payfileadd)
        # print(json.dumps(filelistdata))
        
        # print(filelistname)
        with open( patch_path + '/' + filelistname, 'w') as f:
            json.dump(filelistdata, f)

        command = "cd " + localRepoPath + '\n' + "git apply -R {}".format('localdata' + '/' + PR_id + '/' + patch_file)
        os.system(command)
        # call pagure API to post the corresponding issue
        # call pagure API to post the corresponding issue
        PR_HTML_Link = "https://github.com/{}/{}/pull/{}".format(githubUsername, githubRepo, PR_id)
        pagure_content = """<table>
                                <tr>
                                    <th>Creator</th>
                                    <td>{}</td>
                                </tr>
                                <tr>
                                    <th>PR Link</th>
                                    <td><a href="{}" target="_blank">{}</a></td>
                                </tr>
                                <tr>
                                    <th>Modified File</th>
                                    <td>{}</td>
                                </tr>
                                <tr>
                                    <th>Preview</th>
                                    <td>{}</td>
                                </table><hr>\n\n{}""".format(info['creator'], PR_HTML_Link, PR_HTML_Link, filelist, payfileadd , info['content'])

        pagure.create_issue(pagure_title, pagure_content)

    # PR closed
    elif data['action'] == 'closed':
        # not merged
        if not data['pull_request']['merged']:
            logging.info("Pull request closed with out being merged on GitHub.")
            # call github issue comment list API to get pagure issue id
            r = requests.get("https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername, githubRepo, data['pull_request']['number']),
                             headers=githubHeader)
            data = json.loads(r.text)  # parse API return value
            info_body = data[0]['body']
            pagure_id = int(info_body[8:info_body.find(']')])  # get pagure issue id from the first comment
            pagure.change_issue_status(pagure_id, "Invalid")

        # merged
        else:
            # TODO: is there a more elegant way to do this?
            logging.info("Pull request merged on GitHub.")
            # let Python use shell commands to pull the changes from github, then push changes to pagure
            command = "cd " + localRepoPath + """
            git pull origin master
            git push pagure master
            """
            os.system(command)


def handle_pull_request_comment(post_body):

    data = json.loads(post_body)  # parse web hook payload

    # currently github are not providing comment deletion web hook, so only handle creation
    if data['action'] == 'created':
        logging.info("New comment created on GitHub.")
        info = {'issue_name': data['issue']['title'],
                'issue_id': data['issue']['number'],
                'comment': data['comment']['body'],
                'username': data['comment']['user']['login']}  # get comment info
        # we auto create an comment pointing to pagure when new PR is opened, should ignore this one
        if info['comment'].startswith("[Issue #"):
            return
        # avoid infinity loop
        if info['comment'].startswith("*Commented by"):
            return

        # prepare pagure comment body
        comment_body = """*Commented by {}*
        
        {}""".format(info['username'], info['comment'])
        # call github issue comment list API to get pagure issue id
        r = requests.get("https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername, githubRepo, info['issue_id']),
                         headers=githubHeader)
        data = json.loads(r.text)  # parse API return value
        info_body = data[0]['body']
        pagure_id = int(info_body[8:info_body.find(']')])  # get pagure issue id from the first comment
        # call pagure API to sync the comment
        pagure.comment_issue(pagure_id, comment_body)


# main server class
class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        print(self.headers)
        print(post_body)

        # Validate signature
        sha_name, signature = self.headers['X-Hub-Signature'].split('=')

        if sha_name != 'sha1':
            return
        mac = hmac.new(secretKey.encode(), msg=post_body.encode(), digestmod=hashlib.sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            logging.warning("Ignoring a web hook call due to incorrect signature.")
            return

        # Handle post body
        if self.headers['X-Github-Event'] == 'pull_request':
            th = threading.Thread(target=handle_pull_request, args=(post_body,))
            th.start()

        elif self.headers['X-Github-Event'] == 'issue_comment':
            th = threading.Thread(target=handle_pull_request_comment, args=(post_body,))
            th.start()


myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Syncing tool")
logging.basicConfig(filename='github.log', level=logging.INFO)
logging.info('Server starts ay %s:%s.', listenAddr, listenPort)

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
logging.info('Server stops.')
