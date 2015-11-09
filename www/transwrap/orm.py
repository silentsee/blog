#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'xieshaoxin'
import logging
import db
import time

class Column(object):
    """
    """

    _count = 0

    def __init__(self, **kw):
        self.name = kw.get('name', None)  # 使用get(xx,None)不会产生Keyerror
        self.type = kw.get('type', '')  # varchar(255)
        self.primary_key = kw.get('primary_key', False)
        self.nullable = kw.get('nullable', False)
        self.insertable = kw.get('insertable', True)
        self.updatable = kw.get('updatable', True)
        self._default = kw.get('default', None)
        self._order = Column._count #用于__sql__()生成语句里，column的顺序固定顺序
        Column._count += 1

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default


class IntegerField(Column):
    """
    有了 class IntegerField 就可以不用写成这样：id = Column({'name': 'id', 'type': 'int', 'primary_key': True, 'nullable': False})
    做到了 DRY（Don't Repeat Yourself）写成 id = IntegerField(primary_key=True)，只有需要修改的属性需要传参，把type固定下来了
    """

    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0
        if 'type' not in kw:
            kw['type'] = 'bigint'
        super(IntegerField, self).__init__(**kw)


class StringField(Column):
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'type' not in kw:
            kw['type'] = 'varchar(255)'
        super(StringField, self).__init__(**kw)


class FloatField(Column):
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0.0
        if 'type' not in kw:
            kw['type'] = 'real'
        super(FloatField, self).__init__(**kw)

_triggers = frozenset(['pre_insert', 'pre_update', 'pre_delete'])

class ModelMetaclass(type):
    """
    mataclass 做以下事情：
    获取model类的子类的attr，如user的属性存储在__mappings__里，就是说将user表的结构存在mappings里；
    然后把user里的key－》表结构 清掉，用来存储值key－》value

    """

    def __new__(mcs, name, base, attrs):
        if name == 'Model':
            return type.__new__(mcs, name, base, attrs)
        mappings = dict()
        primary_key = None
        for k, v in attrs.iteritems():
            if isinstance(v, Column):
                if not v.name:
                    v.name = k
                logging.info("Found mapping: %s ==> %s" % (k, v))
                mappings[k] = v
                if v.primary_key:
                    primary_key = v
                    # 这里直接 attrs.pop(k)会 RuntimeError: dictionary changed size during iteration，还要写一个循环
        for k in mappings.iterkeys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings  # 在model的类方法里使用
        if not '__table__' in attrs:
            attrs['__table__'] = name.lower() # 同上
        attrs['__primary_key__'] = primary_key
        for t in _triggers:
            if t not in attrs:
                attrs[t] = None
        return type.__new__(mcs, name, base, attrs)  # 创建特殊的Model类，如果是User则该model保存的是user的mapping


"""
继承dict是因为使用dict的初始化方法，保存名值对,表示数据库的记录
"""


class Model(dict):
    """
    提供db操作的类
    >>> class User(Model):
    ...     id = IntegerField(primary_key=True)
    ...     name = StringField()
    ...     email = StringField(updatable=False)
    ...     passwd = StringField(default=lambda: '******')
    ...     last_modified = FloatField()
    ...     def pre_insert(self):
    ...         self.last_modified = time.time()
    >>> u = User(id=10190, name='Michael', email='orm@db.org')
    >>> r = u.insert()
    >>> u.email
    'orm@db.org'
    >>> u.passwd
    '******'
    >>> u.last_modified > (time.time() - 2)
    True
    >>> f = User.get(10190)
    >>> f.name
    u'Michael'
    >>> f.email
    u'orm@db.org'
    >>> f.email = 'changed@db.org'
    >>> r = f.update() # change email but email is non-updatable!
    >>> len(User.find_all())
    1
    >>> g = User.get(10190)
    >>> g.email
    u'orm@db.org'
    >>> r = g.delete()
    >>> len(db.select('select * from user where id=10190'))
    0
    >>> import json
    >>> print User().__sql__()
    -- generating SQL for user:
    create table `user` (
      `id` bigint not null,
      `name` varchar(255) not null,
      `email` varchar(255) not null,
      `passwd` varchar(255) not null,
      `last_modified` real not null,
      primary key(`id`)
    );
    """

    __metaclass__ = ModelMetaclass

    @classmethod
    def __sql__(cls):
        """
        返回该表建表的sql语句的list
        """
        sql = list()
        sql.append('-- generating SQL for %s:' % cls.__table__)
        sql.append('create table `%s` (' % cls.__table__)
        for v in sorted(cls.__mappings__.values(), lambda x, y: cmp(x._order, y._order)):
            sql.append("  `%s` %s %s," %(v.name,v.type, "not null" if  not v.nullable else ""))
        sql.append('  primary key(`%s`)' % cls.__primary_key__.name)
        sql.append(');')
        return '\n'.join(sql)

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'%s' object has no attribute %s" % (self.__table__, item))

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    def get(cls, primary_key):
        """
        返回cls的对象
        """
        #return db.select_one('select * from %s where %s =?' % (cls.__table__, cls.__primary_key__.name), primary_key)
        r = db.select_one('select * from %s where %s =?' % (cls.__table__, cls.__primary_key__.name), primary_key)
        return cls(**r) if r else None

    def insert(self):
        """
        返回受影响的行数
        """
        self.pre_insert and self.pre_insert()
        params = dict()
        for k, v in self.__mappings__.iteritems():
            if v.insertable:
                if not hasattr(self, k):
                    setattr(self, k, v.default)
                params[v.name] = getattr(self, k)
        return db.insert(self.__table__, **self)

    @classmethod
    def find_all(cls):
        #return db.select('select * from `%s`' % cls.__table__) #这样写返回的不是User或者具体的表对象,而是由dict组成的list
        l = db.select('select * from `%s`' % cls.__table__)
        return [ cls(**d) for d in l ] #这样写，返回的就是由对象组成的list

    def delete(self):
        self.pre_delete and self.pre_delete() #这里用一种逻辑短路的写法，若pre_delete为空，则跳过
        pk = self.__primary_key__.name
        db.delete('delete from `%s` where %s=?' % (self.__table__, self.__primary_key__.name), getattr(self,pk))
        return self



class User(Model):
    """
    如果我在User里写了insert方法，get方法，delete方法等
    那么如果有一个的表，比如Blog表，那么我仍然要写一个同样的方法，这些方法的参数都是一样的，都是列名值对来表示的记录。
    此时有以下选择：
    1.对方法进行封装：
    user.id = 1234
    blog.id = 5678
    insert(user,"user")将user插入到'user'表
    insert(blog)
    get(user)
    get(blog)
    但这样其实只是把代码写在了函数里，代码量并没有减少，或者说还是重复了，这个选择也并不符合面对对象程序设计
    2.用对象来封装：
    user.id =1234
    blog.id =5678
    user.insert()
    blog.insert()
    要这样写则该对象负责实现insert等方法，而方法调用在user等类上，该类为user，blog的父类
    那么，父类如何获取子类的字段呢？
    使用元类
    """
    __table__ = 'user'
    id = IntegerField(primary_key=True)  # uuid形式
    name = StringField()  # 存储char
    email = StringField()  # 存储char
    passwd = StringField()  # 存储char TODO：默认必须非明文存储
    last_modified = FloatField()


if __name__ == '__main__':  # 测试时运行
    logging.basicConfig(level=logging.DEBUG)  # 将日志级别设为debug
    db.create_engine('root', 'root', 'test')  # 创建数据库引擎
    db.update('drop table if exists user')  # 创建user表用来测试
    db.update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    import doctest
    doctest.testmod()
