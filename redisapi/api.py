# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os

import flask

from flask import request
from managers import SharedManager, DockerManager, DockerHaManager, FakeManager
from plans import active as active_plans
from storage import MongoStorage


app = flask.Flask(__name__)
app.debug = os.environ.get('DEBUG', '0') in ('true', 'True', '1')


def manager_by_instance(instance):
    plans = {
        'development': SharedManager,
        'basic': DockerManager,
        'plus': DockerHaManager,
    }
    return plans[instance.plan]()


def manager_by_plan_name(plan_name):
    plans = {
        'development': SharedManager,
        'basic': DockerManager,
        'plus': DockerHaManager,
    }
    return plans[plan_name]()


@app.route("/resources/<name>/bind-app", methods=["POST"])
def bind_app(name):
    storage = MongoStorage()
    instance = storage.find_instance_by_name(name)
    result = manager_by_instance(instance).bind(instance)
    return json.dumps(result), 201


@app.route("/resources/<name>/bind-app", methods=["DELETE"])
def unbind_app(name):
    FakeManager().unbind()
    return "", 200


@app.route("/resources", methods=["POST"])
def add_instance():
    instance = manager_by_plan_name(request.form['plan']).add_instance(
        request.form['name'])
    from storage import MongoStorage
    storage = MongoStorage()
    storage.add_instance(instance)
    return "", 201


@app.route("/resources/<name>", methods=["DELETE"])
def remove_instance(name):
    from storage import MongoStorage
    storage = MongoStorage()
    instance = storage.find_instance_by_name(name)
    manager_by_instance(instance).remove_instance(instance)
    storage.remove_instance(instance)
    return "", 200


@app.route("/resources/<name>/status", methods=["GET"])
def status(name):
    from storage import MongoStorage
    storage = MongoStorage()
    instance = storage.find_instance_by_name(name)
    ok, msg = manager_by_instance(instance).is_ok()
    if ok:
        return msg, 204
    return msg, 500


@app.route("/resources/plans", methods=["GET"])
def plans():
    return json.dumps(active_plans()), 200
