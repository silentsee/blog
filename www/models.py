#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'xieshaoxin'


from transwrap.db  import next_id
from transwrap.orm import FloatField,Model,StringField,BooleanFiled,IntegerField,TextField
import time

class User(Model):
    __table__ = 'user'

    id = StringField(primary_key=True, default=next_id(), type="varchar(50)")
    name = StringField(type='varchar(50)')
    email = StringField(updatable=False, type='varchar(50)')
    admin = BooleanFiled()
    passwd = StringField(type="varchar(50)")
    created_at = FloatField(updatable=False, default=time.time)
    image = StringField(type='varchar(500)')


class Blog(Model):
    __table__ = 'blog'

    id = StringField(primary_key=True, default=next_id(), type="varchar(50)")
    user_id = StringField(updatable=False,type="varchar(50)")
    user_name = StringField(type='varchar(50)')
    user_image = StringField(type='varchar(500)')
    summary = StringField(type='varchar(200)')
    name = StringField(type="varchar(50)")
    content = TextField()
    created_at = FloatField(updatable=False, default=time.time)


class Comment(Model):
    __table__ = 'comment'
    id = StringField(primary_key=True, default=next_id(), type="varchar(50)")
    user_id = StringField(updatable=False,type="varchar(50)")
    user_name = StringField(type='varchar(50)')
    user_image = StringField(type='varchar(500)')
    blog_id = StringField(updatable=False,type="varchar(50)")
    content = TextField()
    created_at = FloatField(updatable=False, default=time.time)

if __name__ == '__main__':
    print User().__sql__()
    print Blog.__sql__()
    print Comment.__sql__()