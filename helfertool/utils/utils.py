#!/usr/bin/python
# -*- coding: utf-8 -*-
from jinja2 import Environment, FileSystemLoader

from flask import render_template




# jinja_env = Environment(loader=FileSystemLoader(config.templates),autoescape=True)





## shouldn't be here..
import os
import subprocess


def run_command_output(cmd):
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	return p.stdout.read()

invalid_form_default_msg = u"""Du hast ein oder mehrere Felder des Formulars mit fehlerhaften Daten abgeschickt. Bitte geh zurück und korrigiere eventuell falsche Felder."""
def invalid_form_error(session, msg=invalid_form_default_msg):
	return render_template("error.xml", error_short = "Fehlerhafte Felder", error_long = msg, session=session)
