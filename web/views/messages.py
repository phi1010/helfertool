# -*- coding: utf-8 -*-

import datetime

from web.utils import render_template, expose, url_for, run_command_output, invalid_form_error
from web.login_utils import require_login, is_user_logged_in
from web.message_utils import send_message
from werkzeug import redirect
from werkzeug.wrappers import Request
import web.utils
import db
import config

#meh, get message digest via ajax, everything else would be way more hacky
@expose('/messages/digest')
def messages_deliverAjax(request):
	if not is_user_logged_in(request.session): ##nicht auf dinge weiterleiten, die kein ajax sind
		return render_template('empty.xml', session=request.session)
	userid = request.session["userid"]
	
	matches = db.select("SELECT COUNT(*) as count, title FROM message WHERE receiver = ? AND deliveryTime <= ? AND read = 0",
			(userid, datetime.datetime.now(),))
		
	return render_template('message_digest.xml',
			unreadMessageCount = matches[0]["count"],
			messages = matches,
			session=request.session)

#read message via ajax
@expose('/messages/read/<int:messageid>')
def markAsRead(request, messageid):
	if not is_user_logged_in(request.session):
		return render_template('empty.xml', session=request.session) ##nicht auf dinge weiterleiten, die kein ajax sind
	
	db.update("UPDATE message SET read = 1 WHERE id = ? AND receiver = ?", (messageid, request.session["userid"]))
	return redirect('/')
	
## alle nachrichten anzeigen
@require_login
@expose('/messages/show/')
def messages_show(request):
	matches = db.select("""SELECT message.id as id,
				 message.title as title,
				 message.content as content,
				 message.read as read,
				 person.id as senderid,
				 person.username as sendername
			 FROM message
			 LEFT JOIN person ON message.sender = person.id
			 WHERE message.receiver = ? AND message.deliveryTime <= ?""",
			(request.session["userid"], datetime.datetime.now(),))
		
	return render_template('message_show.xml',
			messageCount = len(matches), messages = matches, session=request.session)
