#!/usr/bin/python

import config
import helfertool.db

from helfertool import app

app.secret_key=config.secret_key

app.run(debug=True)
