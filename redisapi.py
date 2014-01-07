# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import flask

from managers import RedisManager


app = flask.Flask(__name__)


@app.route("/resources/<name>", methods=["POST"])
def bind(name):
    manager = RedisManager()
    result = manager.bind()
    return json.dumps(result), 201


@app.route("/resources/<name>/hostname/<host>", methods=["DELETE"])
def unbind(name, host):
    manager = RedisManager()
    manager.unbind()
    return "", 200


@app.route("/resources", methods=["POST"])
def add_instance():
    manager = RedisManager()
    manager.add_instance()
    return "", 201


@app.route("/resources/<name>", methods=["DELETE"])
def remove_instance(name):
    manager = RedisManager()
    manager.remove_instance()
    return "", 200


@app.route("/resources/<name>/status", methods=["GET"])
def status(name):
    manager = RedisManager()
    ok, msg = manager.is_ok()
    if ok:
        return msg, 204
    return msg, 500
