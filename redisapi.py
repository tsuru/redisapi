# Copyright 2013 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

import flask

app = flask.Flask(__name__)


@app.route("/resources", methods=["POST"])
def add_instance():
    return "", 201

try:
    os.environ["REDIS_SERVER_HOST"]
except KeyError:
    msg = u"You must define the REDIS_SERVER_HOST environment variable."
    raise Exception(msg)
