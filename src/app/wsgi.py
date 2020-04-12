import os

from gevent.pywsgi import WSGIServer

from . import app

http_server = WSGIServer(("0.0.0.0", 5000), app)

if __name__ == "__main__":
    http_server.serve_forever()
