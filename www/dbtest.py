__author__ = 'xieshaoxin'

from models import User, Blog, Comment

from transwrap import db

db.create_engine(user='root', passwd='root', database='blog')

u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

u.insert()

print 'new user id:', u.id

u1 = User.find_first('where email=?', 'test@example.com')
print 'find user\'s name:', u1.name

u1.delete()

u2 = User.find_first('where email=?', 'test@example.com')
print 'find user:', u2