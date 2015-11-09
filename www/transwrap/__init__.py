#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'silentsee'

class field(object):
    def __init__(self, *args):
        pass
    def __str__(self):
        return '<%s>' % (self.__class__.__name__)

class intfield(field):
    pass


class floatfield(field):
    pass

class modelmetaclass(type):
    def __new__(cls,name,bases,attrs):
        if name=='model':
            return type.__new__(cls, name, bases, attrs)
        print('Found model: %s' % name)
        mappings = dict()
        for k, v in attrs.iteritems():
            if isinstance(v, field):
                print('Found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
        for k in mappings.iterkeys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = name # 假设表名和类名一致
        return type.__new__(cls, name, bases, attrs)

print modelmetaclass.__call__

def metaclass(name, base, attrs):
    for (k, v) in attrs.items():
        print('Found : %s ==> %s' % (k, v))
    print name
    print base
    print attrs
    return type(name, base, attrs)


def __new__(cls, name, bases, attrs):
        if name=='model':
            return type.__new__(cls, name, bases, attrs)
        print('Found model: %s' % name)
        mappings = dict()
        for k, v in attrs.iteritems():
            if isinstance(v, field):
                print('Found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
        for k in mappings.iterkeys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = name # 假设表名和类名一致
        return type.__new__(cls, name, bases, attrs)

metaclass.__new__ = __new__

class model(dict):
    __metaclass__ = modelmetaclass

    def __init__(self, **kw):
        super(model, self).__init__(**kw)


class user(model):
    id = intfield(1)
    float = floatfield(2.2)

#u = user(id=4,float=6,fuck=8)
print model.__dict__
print user.__dict__
print '-------------------------------------'

class Field(object):
    def __init__(self, name, column_type):
        self.name = name
        self.column_type = column_type
    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)

class StringField(Field):
    def __init__(self, name):
        super(StringField, self).__init__(name, 'varchar(100)')

class IntegerField(Field):
    def __init__(self, name):
        super(IntegerField, self).__init__(name, 'bigint')

class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        print('Found model: %s' % name)
        mappings = dict()
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                print('Found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
        for k in mappings.iterkeys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = name # 假设表名和类名一致
        return type.__new__(cls, name, bases, attrs)

class Model(dict):
    __metaclass__ = ModelMetaclass

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def save(self):
        fields = []
        params = []
        args = []
        for k, v in self.__mappings__.iteritems():
            fields.append(v.name)
            params.append('?')
            args.append(getattr(self, k, None))
        sql = 'insert into %s (%s) values (%s)' % (self.__table__, ','.join(fields), ','.join(params))
        print('SQL: %s' % sql)
        print('ARGS: %s' % str(args))

# testing code:

class User(Model):
    id = IntegerField('uid')
    name = StringField('username')
    email = StringField('email')
    password = StringField('password')

#u = User(id=12345, name='Michael', email='test@orm.org', password='my-pwd')
print User.__dict__
print Model.__dict__


user = {'id': 1,'name':'alex','fuck':'you','shit':'it','damn':'it'}
mappings = dict()
for k,v in user.iteritems():
    mappings[k] = v
    user.pop(k)

print mappings
print user

print '-----------------------------'
class testdefault(object):

    @property
    def default(self):
        return r"i'm default "

u = testdefault
print u