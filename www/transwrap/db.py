__author__ = 'silentsee'
import logging
class Dict(dict):
    '''
    Simple dict support access as x.y style

    >>> d1 = Dict()
    >>> d1["x"] = 100
    >>> d1.x
    100
    >>> d1.y = 200
    >>> d1.y
    200
    >>> d2 = Dict(a=1,b=2,c="3")
    >>> d2.a
    1
    >>> d2.c
    '3'
    >>> d2['empty']
    Traceback (most recent call last):
        ...
    KeyError: 'empty'
    >>> d2.empty
    Traceback (most recent call last):
        ...
    AttributeError: 'Dict' object has no attribute 'empty'
    '''
    def __init__(self, n=(), v=(),**kw):
        super(Dict,self).__init__(**kw)
        for k, v in zip(n, v):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)
    def __setattr__(self, key, value):
        self[key] = value

class DBError(Exception):
    pass

# global engine object:
engine = None


class _Engine(object):

    def __init__(self, connect):
        self._connect = connect

    def connect(self):
        return self._connect()

def create_engine(user,passwd,database,host='127.0.0.1',port=3306,**kw):
    import mysql.connector
    global engine
    if engine is not None:
        raise DBError('Engine is already initialized.')
    params = dict(user=user, password=passwd, database=database, host=host, port=port)
    defaults = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)
    for k, v in defaults.iteritems():
        params[k] = kw.pop(k, v)
    params.update(kw)
    params['buffered'] = True
    engine = _Engine(lambda: mysql.connector.connect(**params))
    # test connection...
    logging.info('Init mysql engine <%s> ok.' % hex(id(engine)))




if __name__=='__main__':
    import doctest
    doctest.testmod()