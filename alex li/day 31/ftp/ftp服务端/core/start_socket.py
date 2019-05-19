import configparser
import json
import os
import socketserver
import struct
import subprocess
import time

from setting import set


class Mysocket(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            print("连接成功")
            data = self.response()
            self.recv_data = json.loads(data.decode("utf-8"))  # 把接受的json格式加载出来，传过来的是bytes类型，必须编码
            self.check_args()

    def reques(self, cmd):  # 发送数据
        self.request.send(struct.pack('i', len(cmd)))
        print('aasdf')
        self.request.send(cmd)

    def response(self):  # 接收数据
        buffsize = struct.unpack('i', self.request.recv(4))[0]
        return self.request.recv(int(buffsize))

    def check_args(self):  # 执行对应参数
        if hasattr(self, self.recv_data.get("action")):
            func = getattr(self, self.recv_data.get("action"))
            func()  # 运行对应客户端发送过来的检测方法

    def get_user_pass(self):  # 得到用户发送的用户名，密码
        self.client_name = self.recv_data.get("username")
        self.client_password = self.recv_data.get("password")

    def auth(self):  # 认证
        self.get_user_pass()
        cfg = configparser.ConfigParser()
        cfg.read(set.auth_file)
        if self.client_name in cfg.sections():
            if self.client_password == cfg[self.client_name]["password"]:
                info = "{0} login success".format(self.client_name).encode("utf-8")
                self.reques(info)
                self.mainPath = os.path.join(set.Basedir, "home", self.client_name)  # 用户的家目录，所有上传，下载操作在这里
                self.sever_interaction()  # 认证成功后进行交互
            else:
                fail_info = "login fail, please check your username and password again".encode("utf-8")
                self.reques(fail_info)
        else:
            fin_info = "no such user or invalid password".encode("utf-8")
            self.reques(fin_info)

    def sever_interaction(self):  # 客户端和服务端的交互
        while True:
            from_client_msg = self.response().decode("utf-8")
            client_command = json.loads(from_client_msg).get("action")
            if hasattr(self, client_command):
                func = getattr(self, client_command)
                func(**json.loads(from_client_msg))  # 把客户端发过来的命令作为参数传递到每一个执行的函数

    def dir(self, **cmd):
        os.chdir(self.mainPath)
        res = subprocess.Popen("dir", shell=True,
                               stdout=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE)  # subprocess,执行命令的库，其中把结果输出重定向到了subprocess的管道中，需要时再去读取
        err = res.stderr.read()
        if err:
            self.reques(err.decode("gbk"))
        else:
            cmd_out = res.stdout.read()
            # conn.send(cmd_out)
            self.reques(cmd_out)

    def ls(self, **cmd):
        file = os.listdir(self.mainPath)
        self.reques("  ".join(file).encode("utf8"))

    def cd(self, **cmd):
        curdir = os.path.abspath(os.path.curdir)
        target_path = cmd.get("path")
        self.mainPath = os.path.join(self.mainPath, target_path)
        if target_path == "..":
            # if os.path.abspath(os.path.curdir) < self.mainPath:
            #     exit()
            self.reques(os.path.dirname(os.path.dirname(self.mainPath)).encode("utf-8"))
            print(os.path.dirname(os.path.dirname(self.mainPath)))
            os.chdir(os.path.dirname(os.path.dirname(self.mainPath)))

        else:
            try:
                os.chdir(self.mainPath)
                self.reques(self.mainPath.encode("utf-8"))
            except OSError as e:
                self.reques("没有进入该目录的权限".encode("utf-8"))

    def put(self, **cmd):
        has_receive = 0
        if not os.path.exists(os.path.join(self.mainPath, cmd.get("uploadpath"))):  # 检测上次的目录是否存在，不存在就创建
            os.mkdir(os.path.join(self.mainPath, cmd.get("uploadpath")))
        abspath = os.path.join(self.mainPath, cmd.get("uploadpath"), cmd.get("filename"))
        if os.path.exists(abspath) and os.stat(abspath).st_size == cmd.get("file_size"):
            self.reques("500".encode("utf8"))
        elif not os.path.exists(abspath):
            self.reques("404".encode("utf8"))
            f = open(abspath, "wb")
            while has_receive < cmd.get("file_size"):
                data = self.request.recv(1024)
                f.write(data)
                has_receive += 1024
            f.close()
            self.reques("上传完成".encode("utf-8"))
            return
        elif os.path.exists(abspath) and os.stat(abspath).st_size < cmd.get("file_size"):
            self.reques("520".encode("utf8"))
            self.request.send(str(os.stat(abspath).st_size).encode("utf-8"))
            f = open(abspath, "ab")
            has_receive = os.stat(abspath).st_size
            while has_receive < cmd.get("file_size"):
                data = self.request.recv(1024)
                f.write(data)
                has_receive += 1024
            f.close()
            self.reques("续传完成".encode("utf-8"))

    def write_log(self, string):  # 保存错误日志
        os.chdir("..")
        print(os.getcwd())
        if os.path.exists("log"):
            os.chdir("log")
            entitle_time = time.strftime("%Y-%m-%d--%H-%M-%S", time.localtime())
            with open(entitle_time + ".txt", 'w+', encoding="utf-8") as f:
                f.write(str(self.client_address[0]) + "\n")
                f.write(str(string))
