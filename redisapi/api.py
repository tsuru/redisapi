# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import flask
import os

from flask import request
from managers import managers, SharedManager, DockerManager, DockerHaManager
from plans import active as active_plans
from storage import MongoStorage


app = flask.Flask(__name__)


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


def manager():
    manager_name = os.environ.get("API_MANAGER", "shared")
    return managers[manager_name]()


@app.route("/resources/<name>", methods=["POST"])
def bind(name):
    storage = MongoStorage()
    instance = storage.find_instance_by_name(name)
    result = manager_by_instance(instance).bind(instance)
    return json.dumps(result), 201


@app.route("/resources/<name>/hostname/<host>", methods=["DELETE"])
def unbind(name, host):
    manager().unbind()
    return "", 200


@app.route("/resources", methods=["POST"])
def add_instance():
    manager_by_plan_name(request.form['plan']).add_instance(
        request.form['name'])
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


@app.route("/resources/plans", methods=["GET"])
def plans():
    return json.dumps(active_plans()), 200
