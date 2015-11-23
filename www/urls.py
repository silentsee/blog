#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import Blog, User, Comment
from transwrap.web import  view, get



@view("test_users.html")
@get('/test/:id')
def getbyid(id):
    user = User.get(primary_key=id)
    users = User.find_all()
    return dict(users=users, user=user)


@view('blogs.html')
@get('/')
def index():
    blogs = Blog.find_all()
    # 查找登陆用户:
    user = User.find_first('where email=?', 'admin@example.com')
    return dict(blogs=blogs, user=user)