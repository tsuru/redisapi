# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os


class Instance(object):

    def __init__(self, host, container_id, port, name):
        self.host = host
        self.container_id = container_id
        self.port = port
        self.name = name

    def to_json(self):
        return {
            'host': self.host,
            'container_id': self.container_id,
            'port': self.port,
            'name': self.name
        }


class MongoStorage(object):

    def conn(self):
        mongodb_host = os.environ.get("MONGODB_HOST", "localhost")
        mongodb_port = int(os.environ.get("MONGODB_PORT", 27017))

        from pymongo import MongoClient
        return MongoClient(host=mongodb_host, port=mongodb_port)

    def add_instance(self, instance):
        self.conn()['redisapi']['instances'].insert(instance.to_json())

    def find_instance_by_name(self, name):
        result = self.conn()['redisapi']['instances'].find_one({"name": name})
        return Instance(
            host=result['host'],
            container_id=result['container_id'],
            port=result['port'],
            name=result['name']
        )

    def remove_instance(self, instance):
        return self.conn()['redisapi']['instances'].remove(
            {"name": instance.name})
