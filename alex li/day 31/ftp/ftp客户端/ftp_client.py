import getpass
import json
import optparse
import os
import socket
import struct
import sys


class Client:
    def __init__(self):
        self.op = optparse.OptionParser()  # 调用optparse中的optionparse方法，记得加上括号
        self.op.add_option("-c", "--connect", dest="connect")
        self.op.add_option("-p", '--port', dest="port")
        self.option, self.args = self.op.parse_args()
        # print(self.option)                                                   # 字典形式
        # print(self.args)                                                     # 列表形式
        self.res = self.check_port(self.option)  # 把检查端口后的结果接收
        self.make_connect(self.option)  # 在把接收到的ip和端口号拿去建立链接。
        self.mainPath = os.path.dirname(os.path.abspath(__file__))  # 用户的路径，方便后面用户在他自己的目录下新建目录传东西
        self.last = 0
        exec_res = self.auth()
        if exec_res:
            self.client_interaction()
        else:
            self.auth()

    def check_port(self, option):
        connect_port = int(option.port)
        if connect_port <= 0 or connect_port >= 65535:
            print("端口号有误，请重新输入，范围是0-65535")
            return False
        else:
            return True

    def make_connect(self, option):
        self.client = socket.socket()
        if self.res:
            ip = option.connect
            port = option.port
            self.client.connect((ip, int(port)))
        else:
            exit()  # 如果会话建立不成功则直接退出

    def request(self, cmd):
        self.client.send(struct.pack('i', len(cmd)))
        self.client.send(cmd.encode('utf-8'))

    def response(self):
        buffsize = struct.unpack('i', self.client.recv(4))[0]
        self.sever_reture_msg = self.client.recv(int(buffsize))

    def auth(self):
        while True:
            self.username = input("input username: ")
            password = getpass.getpass("input password: ")
            if (self.username == "exit" or password == "exit"):
                exit()
            data = {
                "action": "auth",
                "username": self.username,
                "password": password
            }
            while self.username:
                send_data = json.dumps(data)
                self.request(send_data)
                self.response()
                if 'success' in self.sever_reture_msg.decode('utf-8'):
                    print(self.sever_reture_msg.decode('utf-8'))
                    return True
                else:
                    print(self.sever_reture_msg.decode('utf-8'))
                    break

    def client_interaction(self):
        while True:
            cmd = input("{0}>>>:".format(self.username))
            cmd_each = cmd.split(" ")  # 获得cmd总的每一个元素
            if cmd == "exit()":
                exit()
            if cmd.strip() == "put":
                print("no such usage")
            if len(cmd) == 0:  # 当没有输入任何命令，直接敲回车时跳回输入
                continue
            else:
                if hasattr(self, cmd.split(" ")[0]):
                    func = getattr(self, cmd.split(" ")[0])
                    func(cmd_each)
                else:
                    print("no such command")

    def ls(self, cmd):
        if cmd:
            data = {
                "action": "ls",
            }
            self.request(json.dumps(data))
            self.response()
            print(self.sever_reture_msg.decode("utf-8"))
        else:
            data = {
                "action": "ls",
                "filename": cmd[1]
            }
            self.request(json.dumps(data))

    def dir(self, cmd):
        data = {
            "action": "dir",
        }
        self.request(json.dumps(data))
        self.response()
        print(self.sever_reture_msg.decode("gbk"))

    def cd(self, cmd):
        data = {
            "action": "cd",
            "path": cmd[1]
        }
        self.request(json.dumps(data))
        self.response()
        print(self.sever_reture_msg.decode("utf8"))

    def put(self, cmd):
        has_send = 0
        localpath = os.path.join(self.mainPath, cmd[1])
        filename = os.path.basename(localpath)
        try:
            filesize = os.stat(localpath).st_size
        except FileNotFoundError as e:
            print("没有这个文件")
            return
        data = {
            "action": "put",
            "filename": filename,
            "file_size": filesize,
            "uploadpath": cmd[2]
        }
        self.request(json.dumps(data))
        self.response()
        if str(404) == self.sever_reture_msg.decode("utf-8"):
            with open(localpath, "rb") as f:
                while has_send < filesize:
                    # data=f.read(1024)
                    # self.client.send(data)
                    # has_send += len(data)
                    # self.progress(has_send,filesize)
                    if filesize - has_send > 1024:
                        self.client.send(f.read(1024))
                        has_send += 1024
                        self.progress(has_send, filesize)
                    else:
                        self.client.send(f.read(filesize - has_send))
                        has_send = filesize
                        self.progress(has_send, filesize)
                        self.response()
                        print("\n" + self.sever_reture_msg.decode("utf-8"))
                        return  # 重新回到交互界面
        if str(500) == self.sever_reture_msg.decode("utf-8"):
            print("文件存在")
        if str(520) == self.sever_reture_msg.decode("utf-8"):
            choice = input("文件存在但不完整，是否继续[Y/N]")
            if choice.upper() == "Y":
                has_send = int(self.client.recv(1024).decode("utf-8"))
                with open(localpath, "rb") as f:
                    while has_send < filesize:
                        if filesize - has_send > 1024:
                            self.client.send(f.read(1024))
                            has_send += 1024
                            self.progress(has_send, filesize)
                        else:
                            self.client.send(f.read(filesize - has_send))
                            has_send = filesize
                            self.progress(has_send, filesize)
                            self.response()
                            print("\n" + self.sever_reture_msg.decode("utf-8"))
                            return

    def progress(self, has_send, filesize):
        rate = int(float(has_send) / float(filesize) * 100)
        sys.stdout.write("%s%% %s\r" % (rate, "*" * rate))

        # sys.stdout.flush()


c1 = Client()
