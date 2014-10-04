# -*- coding: utf-8 -*-

import datetime

from ..utils.utils import  run_command_output, invalid_form_error
from ..utils.login_utils import require_login, is_user_logged_in
from ..utils.message_utils import send_message
from flask import redirect, request, render_template, session
from werkzeug.wrappers import Request
import helfertool.utils.utils as utils
import helfertool.db as db
import config

from helfertool import app

#meh, get message digest via ajax, everything else would be way more hacky
@app.route('/messages/digest')
def messages_deliverAjax():
	if not is_user_logged_in(session): ##nicht auf dinge weiterleiten, die kein ajax sind
		return render_template('empty.xml', session=session)
	userid = session["userid"]
	
	matches = db.select("SELECT COUNT(*) as count, title FROM message WHERE receiver = ? AND deliveryTime <= ? AND read = 0",
			(userid, datetime.datetime.now(),))
		
	return render_template('message_digest.xml',
			unreadMessageCount = matches[0]["count"],
			messages = matches,
			session=session)

#read message via ajax
@app.route('/messages/read/<int:messageid>')
def markAsRead(messageid):
	if not is_user_logged_in(session):
		return render_template('empty.xml', session=session) ##nicht auf dinge weiterleiten, die kein ajax sind
	
	db.update("UPDATE message SET read = 1 WHERE id = ? AND receiver = ?", (messageid, session["userid"]))
	return redirect('/')
	
## alle nachrichten anzeigen
@require_login
@app.route('/messages/show/')
def messages_show():
	matches = db.select("""SELECT message.id as id,
				 message.title as title,
				 message.content as content,
				 message.read as read,
				 person.id as senderid,
				 person.username as sendername
			 FROM message
			 LEFT JOIN person ON message.sender = person.id
			 WHERE message.receiver = ? AND message.deliveryTime <= ?""",
			(session["userid"], datetime.datetime.now(),))
		
	return render_template('message_show.xml',
			messageCount = len(matches), messages = matches, session=session)
