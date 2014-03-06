# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os


class Instance(object):

    def __init__(self, name, plan, endpoints):
        self.name = name
        self.plan = plan
        self.endpoints = endpoints

    def to_json(self):
        return {
            'endpoints': self.endpoints,
            'name': self.name,
            'plan': self.plan,
        }


class MongoStorage(object):

    def conn(self):
        mongodb_uri = os.environ.get(
            "MONGODB_URI", "mongodb://localhost:27017/")

        from pymongo import MongoClient
        return MongoClient(mongodb_uri)

    def add_instance(self, instance):
        self.conn()['redisapi']['instances'].insert(instance.to_json())

    def find_instance_by_name(self, name):
        result = self.conn()['redisapi']['instances'].find_one({"name": name})
        return Instance(
            name=result['name'],
            plan=result['plan'],
            endpoints=result['endpoints'],
        )

    def remove_instance(self, instance):
        return self.conn()['redisapi']['instances'].remove(
            {"name": instance.name})
