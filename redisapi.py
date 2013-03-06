# Copyright 2013 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os

import flask
import redis

app = flask.Flask(__name__)

try:
    server = os.environ["REDIS_SERVER_HOST"]
except KeyError:
    msg = u"You must define the REDIS_SERVER_HOST environment variable."
    raise Exception(msg)


def coalesce(default, *args):
    for arg in args:
        val = os.environ.get(arg)
        if val:
            return val
    return default


@app.route("/resources/<name>", methods=["POST"])
def bind(name):
    host = coalesce(server, "REDIS_PUBLIC_HOST")
    port = coalesce("6379", "REDIS_SERVER_PORT")
    result = {
        "REDIS_HOST": host,
        "REDIS_PORT": port,
    }
    pswd = os.environ.get("REDIS_SERVER_PASSWORD")
    if pswd:
        result["REDIS_PASSWORD"] = pswd
    return json.dumps(result), 201


@app.route("/resources/<name>/hostname/<host>", methods=["DELETE"])
def unbind(name, host):
    return "", 200


@app.route("/resources", methods=["POST"])
def add_instance():
    return "", 201


@app.route("/resources/<name>", methods=["DELETE"])
def remove_instance(name):
    return "", 200


@app.route("/resources/<name>/status", methods=["GET"])
def status(name):
    conn = redis.Connection(host=server)
    conn.connect()
    return "", 204
