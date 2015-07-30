from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import datetime
import requests
import os
import uuid
import hmac
import hashlib
import threading
import markdown
from urllib.request import urlopen
import libpagure
import logging
import git_interface as git
import formatter
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
localTicketRepoPath = config.localTicketRepoPath

githubToken = config.githubToken
githubHeader = {"Authorization": "token " + githubToken}
githubUsername = config.githubUsername
githubRepo = config.githubRepo

CIserver = config.ciServer
CIrepopath = config.ciRepoPath

pagure = libpagure.Pagure(pagureToken, pagureRepo)

gitRepository = git.Repository(localRepoPath, "origin", "pagure")  # remote 1 is github ('origin'), remote 2 is pagure
ticketRepository = git.Repository(localTicketRepoPath, "origin", "origin")  # repote 1 and 2 are all pagure ('origin')


# handle new pull request on github
def handle_pull_request(post_body):
    data = json.loads(post_body)  # parse web hook payload

    # new PR opened
    if data['action'] == 'opened':
        logging.info("New pull request opened on GitHub.")
        info = {'title': data['pull_request']['title'],
                'creator': data['pull_request']['user']['login'],
                'id': data['pull_request']['number'],
                'link': data['pull_request']['html_url'],
                'content': data['pull_request']['body'],
                'patch_url': data['pull_request']['patch_url']}  # get github PR info
        user_info = data['pull_request']['user']
        if 'name' not in user_info:
            user_info['name'] = user_info['login']
        if 'email' not in user_info:
            user_info['name'] = "Lei Yang"  # if no user email, use a default account
            user_info['login'] = "yangl1996"
            user_info['email'] = "yltt1234512@gmail.com"
            pagure_title = "#{} {} by {}".format(str(info['id']),
                                                 info['title'],
                                                 info['creator'])  # generate pagure issue title
        else:
            pagure_title = "#{} {}".format(str(info['id']),
                                           info['title'])  # generate pagure issue title
        creator = formatter.User(user_info['login'], user_info['name'], user_info['email'])
        if not info['content']:  # empty PR description
            info['content'] = "*No description provided.*"

        # CI Starts

        pr_id = str(info['id'])  # get github PR id
        # call github api to get modified file list of the PR
        r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}/files".format(githubUsername, githubRepo, pr_id),
                         headers=githubHeader)
        data = json.loads(r.text)  # parse api return value

        # Get Patch of PR
        patch_data = urlopen(info['patch_url'])
        patch_file = '{}.patch'.format(info['id'])
        patch_path = "{}/localdata/{}/".format(localRepoPath, pr_id)
        
        # create dir
        if not os.path.exists(os.path.dirname(patch_path)):
            os.makedirs(os.path.dirname(patch_path))
        
        # save patch
        f = open(patch_path + patch_file, 'w')
        f.write(patch_data.read().decode('utf-8'))
        f.close()

        # apply patch

        gitRepository.apply("localdata/{}/{}".format(pr_id, patch_file))

        # generate modified file list
        filelist = '<code>'
        for changed_file in data:
            filelist += "{}\n".format(changed_file['filename'])
        filelist += "</code>"

        # TODO: dump filelist and on update check
        filelistname = "filelist-pr-{}.json".format(pr_id)
        filelistdata = []
        payfileadd = ' '
        
        for changed_file in data:
            # create path
            filename = changed_file['filename']
            filename_no_extension = filename[:filename.rfind('.')]
            if not os.path.exists(os.path.dirname(CIrepopath + '/' + pr_id + '/' + filename)):
                os.makedirs(os.path.dirname(CIrepopath + '/' + pr_id + '/' + filename))

            markdown.markdownFromFile(input=localRepoPath + '/' + changed_file['filename'],
                                      output="{}/{}/{}.html".format(CIrepopath, pr_id, filename_no_extension),
                                      output_format="html5")
            built = True
            filelistdata.append({'filename': filename,
                                 'built': built,
                                 'builtfile': "{}/{}.html".format(pr_id, filename_no_extension)})
            html_path = "{}/{}/{}.html".format(CIserver, pr_id, filename_no_extension)
            payfileadd += '<tr><th></th><td><a href="{}" target="_blank">{}</a></td></tr>'.format(html_path, filename)

        with open(patch_path + '/' + filelistname, 'w') as f:
            json.dump(filelistdata, f)

        built_time_tag = "Built at " + datetime.datetime.utcnow().strftime("%m/%d/%Y %H:%M UTC")

        # revert patch
        gitRepository.apply("localdata/{}/{}".format(pr_id, patch_file), True)

        # CI ends

        pr_html_link = "https://github.com/{}/{}/pull/{}".format(githubUsername, githubRepo, pr_id)
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
                                </tr>
                                {}
                                </table><hr>\n\n{}""".format(info['creator'], pr_html_link, pr_html_link,
                                                             filelist, built_time_tag, payfileadd, info['content'])

        # call pagure API to post the corresponding issue
        new_issue = formatter.Issue(0, pagure_title, pagure_content, creator)
        new_json_path = localTicketRepoPath + "/" + str(uuid.uuid4().hex)
        new_json = open(new_json_path, 'w')
        new_json.write(new_issue.format_json())
        new_json.close()
        ticketRepository.pull(1)
        ticketRepository.commit("add PR #{}".format(info['id']))
        ticketRepository.push(1)

    # PR closed
    elif data['action'] == 'closed':
        # not merged
        if not data['pull_request']['merged']:
            logging.info("Pull request closed with out being merged on GitHub.")
            # call github issue comment list API to get pagure issue id
            get_url = "https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername,
                                                                                     githubRepo,
                                                                                     data['pull_request']['number'])
            r = requests.get(get_url, headers=githubHeader)
            data = json.loads(r.text)  # parse API return value
            info_body = data[0]['body']
            pagure_id = int(info_body[8:info_body.find(']')])  # get pagure issue id from the first comment
            pagure.change_issue_status(pagure_id, "Invalid")

        # merged
        else:
            logging.info("Pull request merged on GitHub.")

            # let Python use shell commands to pull the changes from github, then push changes to pagure
            gitRepository.pull(1)
            gitRepository.push(2)


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
        comment_body = """*Commented by {}*\n\n{}""".format(info['username'], info['comment'])
        # call github issue comment list API to get pagure issue id
        r = requests.get("https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername,
                                                                                        githubRepo,
                                                                                        info['issue_id']),
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
