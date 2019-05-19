import optparse  # 分析运行命令后的参数
import socketserver

from core import start_socket
from setting import set


class GetCommand:
    def __init__(self):
        self.op = optparse.OptionParser()
        # self.op.add_option("-s", "--start", dest="start")          # 具体使用见一些小总结
        option, args = self.op.parse_args()  # 分析我们输入的参数
        # print(type(args))                                          # 分析出来的args是一个列表对象
        self.check(args)

    def check(self, args):
        cmd = args[0]
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            func()

    def start(self):
        print("starting ...")
        server = socketserver.ThreadingTCPServer((set.ip, set.port), start_socket.Mysocket)
        server.serve_forever()
