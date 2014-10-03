#!/usr/bin/python
# -*- coding: utf-8 -*-
from werkzeug import Response
from werkzeug import Local, LocalManager
from werkzeug.routing import Map, Rule
from jinja2 import Environment, FileSystemLoader

from web.session_utils import is_user_logged_in, is_user_admin

import config
import db

def expose(rule, **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, **kw))
        url_map.add(Rule('/static/<file>', endpoint='static', build_only=True))
        return f
    return decorate

def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)

def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    mimetype='application/xhtml+xml')

def removeMessages(session):
	session["messages"] = []

jinja_env = Environment(loader=FileSystemLoader(config.templates),autoescape=True)

jinja_env.globals['url_for'] = url_for
jinja_env.globals['config'] = config
jinja_env.globals['is_user_logged_in'] = is_user_logged_in
jinja_env.globals['is_user_admin'] = is_user_admin
jinja_env.globals['messages_displayed'] = removeMessages
jinja_env.globals['int'] = int
jinja_env.globals['sorted'] = sorted
jinja_env.globals['unicode'] = unicode

local = Local()
local_manager = LocalManager([local])
application = local('application')

url_map = Map()


## shouldn't be here..
import os
import subprocess


def run_command_output(cmd):
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	return p.stdout.read()

invalid_form_default_msg = u"""Du hast ein oder mehrere Felder des Formulars mit fehlerhaften Daten abgeschickt. Bitte geh zurück und korrigiere eventuell falsche Felder."""
def invalid_form_error(session, msg=invalid_form_default_msg):
	return render_template("error.xml", error_short = "Fehlerhafte Felder", error_long = msg, session=session)
