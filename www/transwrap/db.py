__author__ = 'silentsee'
import threading
class _Engine(object):
    def __init__(self,connect):
        self._connect = connect
    def connect(self):
        return self._connect()

engine = None

class _DbCtx(threading.local)