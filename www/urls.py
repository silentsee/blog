#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import Blog, User, Comment
from transwrap.web import  view, get


@view('test_users.html')
@get('/')
def test_users():
    users = User.find_all()
    return dict(users=users)