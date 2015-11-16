#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sae

import logging; logging.basicConfig(level=logging.INFO)

import os, time
from datetime import datetime

from transwrap import db
from transwrap.web import WSGIApplication, Jinja2TemplateEngine

from config import configs


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


# init wsgi app:
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
template_engine.add_filter('datetime', datetime_filter)

wsgi.template_engine = template_engine

import urls

#wsgi.add_interceptor(urls.user_interceptor)
#wsgi.add_interceptor(urls.manage_interceptor)
wsgi.add_module(urls)




if __name__ == "__main__":
    # init db:
    db.create_engine(**configs['db'])
    wsgi.run()
else:
    import sae
    import sae.const
    db.create_engine(user=sae.const.MYSQL_USER, passwd=sae.const.MYSQL_PASS, database=sae.const.MYSQL_DB, port=int(sae.const.MYSQL_PORT), host=sae.const.MYSQL_HOST)
    application = sae.create_wsgi_app(wsgi.get_wsgi_application())

