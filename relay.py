import os

repo_path = '/Users/yangl1996/Documents/doc-test'

command = "cd " + repo_path + """

git pull origin master
git push pagure master
"""
os.system(command)
