from werkzeug import Request, ClosingIterator, SharedDataMiddleware
from werkzeug.exceptions import HTTPException

from werkzeug.contrib.sessions import FilesystemSessionStore

from web.utils import local, local_manager, url_map
from web.session_utils import validate_session
from web import views

import config

session_store = FilesystemSessionStore(config.sessionstoredir)

class Schicht(object):
	def __init__(self):
		local.application = self
		self.dispatch = SharedDataMiddleware(self.dispatch,
				{'/static': config.staticdir})

	def __call__(self, environ, start_response):
		return self.dispatch(environ, start_response)

	def dispatch(self, environ, start_response):
		local.application = self
		request = Request(environ)

		## this is where we load the cookie if any, or create a new one
		sid = request.cookies.get('kif415-helfer-login')
		if sid is None:
			request.session = session_store.new()
		else:
			request.session = session_store.get(sid)
			if not validate_session(request.session):
				session_store.delete(request.session)
				request.session = session_store.new()
				request.session['logout'] = True

		local.url_adapter = adapter = url_map.bind_to_environ(environ)
		try:
			endpoint, values = adapter.match()
			handler = getattr(views, endpoint)
			response = handler(request, **values)
		except HTTPException, e:
			response = e # XXX hrm? this breaks when setting cookies!

		## this is where we save the cookie, if it needs to be saved
		if 'logout' in request.session and request.session['logout']:
			response.delete_cookie('kif415-helfer-login')
		elif request.session.should_save:
			session_store.save(request.session)
			response.set_cookie('kif415-helfer-login', request.session.sid)

		return ClosingIterator(response(environ, start_response),
				[local_manager.cleanup])
