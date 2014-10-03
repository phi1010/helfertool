#!/usr/bin/python


from werkzeug import script
from werkzeug.debug import DebuggedApplication

import db


def make_app():
	from web.application import Schicht
	return DebuggedApplication(Schicht(), evalex=True)


action_runserver = script.make_runserver(make_app, use_reloader=True)

script.run()
