#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, threading
import functools, time, uuid

__author__ = 'silentsee'


class Dict(dict):
    """
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
    """

    def __init__(self, n=(), v=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(n, v):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def next_id(t=None):
    '''
    Return next id as 50-char string.

    Args:
        t: unix timestamp, default to None and using time.time().
    '''
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t * 1000), uuid.uuid4().hex)


class DBError(Exception):
    pass


class MultiColumnsError(DBError):
    pass


# global engine object:
engine = None


class _Engine(object):
    def __init__(self, connect):
        self._connect = connect

    def connect(self):
        return self._connect()


def create_engine(user, passwd, database, host='127.0.0.1', port=3306, **kw):
    try:
        from  mysql.connector import connect
        params = dict(user=user, password=passwd, database=database, host=host, port=port)
        defaults = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)
        params['buffered'] = True
    except ImportError:
        from MySQLdb import connect
        params = dict(user=user, passwd=passwd, db=database, host=host, port=int(port))
        defaults = dict(use_unicode=True, charset='utf8')

    global engine
    if engine is not None:
        raise DBError('Engine is already initialized.')
    for k, v in defaults.iteritems():
        params[k] = kw.pop(k, v)
    params.update(kw)
    logging.info("config user: %s, passwd= %s, database= %s, host= %s,port= %s" %(user, passwd, database, host, port))
    engine = _Engine(lambda: connect(**params))
    # test connection...
    logging.info('Init mysql engine <%s> ok.' % hex(id(engine)))


class _LazyConnection(object):
    """
    当进行具体的数据库操作cursor时，才进行连接
    提供cursor commit rollback cleanup操作
    """

    def __init__(self):
        self.connection = None

    def cursor(self):
        if self.connection is None:
            connection = engine.connect()
            logging.info('open connection <%s>...' % hex(id(connection)))
            self.connection = connection
        return self.connection.cursor()

    def commit(self):
        return self.connection.commit()

    def rollback(self):
        return self.connection.rollback()

    def cleanup(self):
        if self.connection:
            connection = self.connection
            logging.info('close connection <%s>...' % hex(id(connection)))
            self.connection = None
            connection.close()


class _DbCtx(threading.local):
    """
    _DbCtx object holds the connection info
    """

    def __init__(self):
        self.connection = None
        self.transactions = 0

    def is_init(self):
        return not self.connection is None

    def init(self):
        logging.info("open lazy connection")
        self.connection = _LazyConnection()
        self.transactions = 0

    def cleanup(self):
        self.connection.cleanup()
        self.connection = None

    def cursor(self):
        return self.connection.cursor()


# thread local dbctx
_db_ctx = _DbCtx()


class _ConnectionCtx(object):
    """
    _ConnectionCtx object that can open and close connection context. _ConnectionCtx object can be nested and only the most
    outer connection has effect.
    with connection():
        pass
        with connection():
            pass
    """

    def __enter__(self):
        self.should_be_cleanup = False
        global _db_ctx
        if not _db_ctx.is_init():
            self.should_be_cleanup = True
            _db_ctx.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _db_ctx
        if self.should_be_cleanup:
            _db_ctx.cleanup()


def connection():
    """
    return a context object that can be used by with statement

    with connection():
        pass
    """
    return _ConnectionCtx()


def with_connection(func):
    """
    decorator for update and select

    @with_connection
    def foo(*a,**kw):
        foo1()
        foo2()
    """

    @functools.wraps(func)
    def _wrapper(*a, **kw):
        with _ConnectionCtx():
            return func(*a, **kw)

    return _wrapper


@with_connection
def testconnection():
    global _db_ctx
    cursor = _db_ctx.connection.cursor()


# @with_connection
# def update(sql):
#     pass
#
#
# @with_connection
# def select(sql):
#     pass
#
# @with_connection
# def select_one(sql):
#     pass


def _select(sql, first, *args):
    """
     execute select SQL and return unique result or list results.
      记录以列表的形式返回 [Dict(names, x) for x in cursor.fetchall()] = {u'passwd': u'back-to-earth', u'email': u'wall.e@test.org', u'last_modified': 1445794250.081187, u'id': 200, u'name': u'Wall.E'}
    """
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, args)
        if cursor.description:
            names = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names, values)
        return [Dict(names, x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()


@with_connection
def select_one(sql, *args):
    '''
    Execute select SQL and expected one result.
    If no result found, return None.
    If multiple results found, the first one returned.
    >>> u1 = dict(id=100, name='Alice', email='alice@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> u2 = dict(id=101, name='Sarah', email='sarah@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> insert('user', **u2)
    1
    >>> u = select_one('select * from user where id=?', 100)
    >>> u.name
    u'Alice'
    >>> select_one('select * from user where email=?', 'abc@email.com')
    >>> u2 = select_one('select * from user where passwd=? order by email', 'ABC-12345')
    >>> u2.name
    u'Alice'
    '''
    return _select(sql, True, *args)


@with_connection
def select_int(sql, *args):
    '''
    Execute select SQL and expected one int and only one int result.
    >>> n = update('delete from user')
    >>> u1 = dict(id=96900, name='Ada', email='ada@test.org', passwd='A-12345', last_modified=time.time())
    >>> u2 = dict(id=96901, name='Adam', email='adam@test.org', passwd='A-12345', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> insert('user', **u2)
    1
    >>> select_int('select count(*) from user')
    2
    >>> select_int('select count(*) from user where email=?', 'ada@test.org')
    1
    >>> select_int('select count(*) from user where email=?', 'notexist@test.org')
    0
    >>> select_int('select id from user where email=?', 'ada@test.org')
    96900
    >>> select_int('select id, name from user where email=?', 'ada@test.org')
    Traceback (most recent call last):
        ...
    MultiColumnsError: Expect only one column.
    '''
    d = _select(sql, True, *args)
    if len(d) != 1:
        raise MultiColumnsError('Expect only one column.')
    return d.values()[0]


@with_connection
def select(sql, *args):
    '''
    Execute select SQL and return list or empty list if no result.
    >>> u1 = dict(id=200, name='Wall.E', email='wall.e@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> u2 = dict(id=201, name='Eva', email='eva@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> insert('user', **u2)
    1
    >>> L = select('select * from user where id=?', 900900900)
    >>> L
    []
    >>> L = select('select * from user where id=?', 200)
    >>> L[0].email
    u'wall.e@test.org'
    >>> L = select('select * from user where passwd=? order by id desc', 'back-to-earth')
    >>> L[0].name
    u'Eva'
    >>> L[1].name
    u'Wall.E'
    '''
    return _select(sql, False, *args)


@with_connection
def _update(sql, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _db_ctx.transactions == 0:
            # no transaction enviroment:
            logging.info('auto commit')
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()


def insert(table, **kw):
    '''
    Execute insert SQL.
    >>> u1 = dict(id=2000, name='Bob', email='bob@test.org', passwd='bobobob', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> u2 = select_one('select * from user where id=?', 2000)
    >>> u2.name
    u'Bob'
    >>> insert('user', **u2)
    Traceback (most recent call last):
      ...
    IntegrityError: 1062 (23000): Duplicate entry '2000' for key 'PRIMARY'
    '''
    cols, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (
        table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)


def update(sql, *args):
    r'''
    Execute update SQL.
    >>> u1 = dict(id=1000, name='Michael', email='michael@test.org', passwd='123456', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> u2 = select_one('select * from user where id=?', 1000)
    >>> u2.email
    u'michael@test.org'
    >>> u2.passwd
    u'123456'
    >>> update('update user set email=?, passwd=? where id=?', 'michael@example.org', '654321', 1000)
    1
    >>> u3 = select_one('select * from user where id=?', 1000)
    >>> u3.email
    u'michael@example.org'
    >>> u3.passwd
    u'654321'
    >>> update('update user set passwd=? where id=?', '***', '123\' or id=\'456')
    0
    '''
    return _update(sql, *args)


def delete(sql, *args):
    """
    Execute delete SQL.
    >>> u1 = dict(id=2015, name='see', email='bob@test.org', passwd='bobobob', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> delete('delete from user where id=?', 2015)
    1
    >>> insert('user',**u1)
    1
    >>> u1['id'] = 2016
    >>> u1['name'] = "see"
    >>> insert('user',**u1)
    1
    >>> delete("delete from user where name=?",'see')
    2
    >>> delete("delete from user where name=?",'fuck')
    0
    >>> select_int('select count(*) from user')  == delete("delete from user")
    True
    """
    return _update(sql,*args)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    create_engine('root', 'root', 'test')
    update("drop table if exists User")
    update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    # testconnection()
    import doctest

    doctest.testmod()

