# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import flask
import os

from flask import request
from managers import managers


app = flask.Flask(__name__)


def manager():
    manager_name = os.environ.get("API_MANAGER", "shared")
    return managers[manager_name]()


@app.route("/resources/<name>", methods=["POST"])
def bind(name):
    result = manager().bind(name)
    return json.dumps(result), 201


@app.route("/resources/<name>/hostname/<host>", methods=["DELETE"])
def unbind(name, host):
    manager().unbind()
    return "", 200


@app.route("/resources", methods=["POST"])
def add_instance():
    manager().add_instance(request.form['name'])
    return "", 201


@app.route("/resources/<name>", methods=["DELETE"])
def remove_instance(name):
    manager().remove_instance(name)
    return "", 200


@app.route("/resources/<name>/status", methods=["GET"])
def status(name):
    ok, msg = manager().is_ok()
    if ok:
        return msg, 204
    return msg, 500
