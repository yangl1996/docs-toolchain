import os


class Repository:
    def __init__(self, path, remote_1, remote_2):
        self.__path = path
        self.__remote_1 = remote_1
        self.__remote_2 = remote_2

    def pull(self, remote_index):
        remote = ""
        if remote_index == 1:
            remote = self.__remote_1
        elif remote_index == 2:
            remote = self.__remote_2
        command = """cd {} \n git checkout master \n git pull {} \n""".format(self.__path, remote)
        os.system(command)

    def push(self, remote_index):
        remote = ""
        if remote_index == 1:
            remote = self.__remote_1
        elif remote_index == 2:
            remote = self.__remote_2
        command = """cd {} \n git checkout master \n git push {} \n""".format(self.__path, remote)
        os.system(command)

    def commit(self, message):
        command = """cd {} \n git stage --all \n git commit -m "{}" \n""".format(self.__path, message)
        os.system(command)
