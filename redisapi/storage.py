# Copyright 2015 redisapi authors. All rights reserved.
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

    def db(self):
        mongodb_uri = os.environ.get(
            "MONGODB_URI", "mongodb://localhost:27017/")
        database_name = os.environ.get("DATABASE_NAME", "redisapi")

        from pymongo import MongoClient
        return MongoClient(mongodb_uri)[database_name]

    def add_instance(self, instance):
        self.db().instances.insert(instance.to_json())

    def find_instance_by_name(self, name):
        result = self.db().instances.find_one({"name": name})
        return Instance(
            name=result['name'],
            plan=result['plan'],
            endpoints=result['endpoints'],
        )

    def find_instances_by_host(self, host):
        result = self.db().instances.find({"endpoints.host": host})
        instances = []
        for item in result:
            instance = Instance(name=item['name'],
                                plan=item['plan'],
                                endpoints=item['endpoints'])
            instances.append(instance)
        return instances

    def remove_instance(self, instance):
        return self.db().instances.remove({"name": instance.name})
