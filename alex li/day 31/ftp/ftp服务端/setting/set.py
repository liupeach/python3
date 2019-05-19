import os

ip = "127.0.0.1"
port = 8081
auth_file = os.path.join(os.path.dirname(__file__), "user_password.cfg")

Basedir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
