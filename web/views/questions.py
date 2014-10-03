# -*- coding: utf-8 -*-

from web.utils import render_template, expose, url_for, run_command_output, invalid_form_error
from web.login_utils import require_login

from werkzeug import redirect
import web.utils
import db
import config

## frage stellen
@require_login
@expose('/questions/ask')
def questions_ask(request):
	if request.method == "GET":	
		return render_template('questions_ask.xml', session=request.session)
	
	title = request.form.get('title')
	question = request.form.get('text')
	thread_id = request.form.get('thread_id')
	
	
	if not db.sane_str((title,question), True):
		return invalid_form_error(request.session,
				msg=u"titel oder fragentext enthalten ungültige zeichen")

	if not thread_id:
		thread_id = db.insert('INSERT INTO question_threads (title) VALUES (?)', (title,))
	else:
		if not db.sane_int(thread_id):
			return invalid_form_error(request.session,
					msg=u"hast du versucht an der thread_id rumzuspielen?  das is auf jeden fall kein int..")
	
	db.insert('INSERT INTO question (title, text, asking_person, thread_id) VALUES (?, ?, ?, ?)',
				(title, question, request.session["userid"], thread_id))
	
	return redirect("/questions/{}".format(thread_id))

@require_login
@expose('/questions/answer/<int:questionid>')
def questions_answer(request, questionid):
	if request.method == "GET":
		return redirect("/questions")

	tid = db.select('SELECT thread_id FROM question WHERE id = ?', (questionid,))

	if len(tid) == 0:
		return redirect("/questions")
	else:
		tid = tid[0][0]

	answer = request.form.get('text')
	if not db.sane_str(answer, True):
		return invalid_form_error(request.session,
				msg=u"antworttext leer oder enthält ungültige zeichen")

	db.insert('INSERT INTO answer (question, text, thread_id) VALUES (?,?,?)',
			(questionid, answer, tid))

	return redirect("/questions/{}".format(tid))


## thread zu der einen frage
@expose('/questions/<int:thread_id>')
def question_thread(request, thread_id):
	matches = db.select("""SELECT
				question_threads.title AS ttitle,
				question.id AS qid,
				question.title AS qtitle,
				question.text AS qtext,
				answer.text AS atext,
				answer.id AS aid,
				question.asking_person AS asker
			FROM
				question_threads
			JOIN
				question ON question.thread_id = question_threads.id
			LEFT OUTER JOIN
				answer ON answer.question = question.id
			WHERE
			 	question_threads.id = ? 
			ORDER BY
			 	question.id ASC""", (thread_id,))

	return render_template('questions_thread.xml', title=matches[0]["ttitle"], tid=thread_id, frage=matches, session=request.session)

## gestellte fragen, alle
@expose('/questions')
def questions_overview(request):
	matches = db.select("""SELECT
				question_threads.id AS tid,
				question_threads.title AS ttitle,
				(SELECT COUNT(*) FROM question WHERE thread_id = question_threads.id) AS qcount,
				(SELECT COUNT(*) FROM answer WHERE thread_id = question_threads.id) AS acount
			FROM
				question_threads
			""")
	
	unanswered = db.select("""SELECT
					question.thread_id as tid,
					question.id as qid,
					question.title AS qtitle,
					COUNT(answer.question) AS checker
				FROM 
					question
				LEFT JOIN
					answer ON answer.question = question.id
				GROUP BY
					question.id
				HAVING
					checker = 0""")
	
	return render_template('questions.xml', questions=matches, unanswered=unanswered, session=request.session)
