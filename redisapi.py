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


class FakeManager(object):
    instance_added = False
    binded = False

    def add_instance(self):
        self.instance_added = True

    def bind(self):
        self.binded = True


class RedisManager(object):
    def add_instance(self):
        pass

    def bind(self):
        host = coalesce(server, "REDIS_PUBLIC_HOST")
        port = coalesce("6379", "REDIS_SERVER_PORT")
        result = {
            "REDIS_HOST": host,
            "REDIS_PORT": port,
        }
        pswd = os.environ.get("REDIS_SERVER_PASSWORD")
        if pswd:
            result["REDIS_PASSWORD"] = pswd
        return result

    def unbind(self):
        pass

    def remove_instance(self):
        pass

    def status(self):
        passwd = os.environ.get("REDIS_SERVER_PASSWORD")
        kw = {"host": server}
        if passwd:
            kw["password"] = passwd
        try:
            conn = redis.Connection(**kw)
            conn.connect()
        except Exception as e:
            return str(e), 500
        return "", 204


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
    return manager.status()
