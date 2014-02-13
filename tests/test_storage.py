# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import os

from redisapi.storage import Instance


class InstanceTest(unittest.TestCase):

    def test_instance(self):
        host = "host"
        id = "id"
        name = "name"
        port = "port"
        plan = "plan"
        endpoints = [{"port": port, "host": host, "container_id": id}]
        instance = Instance(
            name=name,
            plan=plan,
            endpoints=endpoints,
        )
        self.assertEqual(instance.name, name)
        self.assertEqual(instance.plan, plan)
        self.assertListEqual(instance.endpoints, endpoints)

    def test_to_json(self):
        host = "host"
        id = "id"
        name = "name"
        port = "port"
        plan = "plan"
        endpoints = [{"port": port, "host": host, "container_id": id}]
        instance = Instance(
            name=name,
            plan=plan,
            endpoints=endpoints,
        )
        expected = {
            'name': name,
            'plan': plan,
            'endpoints': endpoints,
        }
        self.assertDictEqual(instance.to_json(), expected)


class MongoStorageTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_host_environ(self, mongo_mock):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host="localhost", port=27017)

        os.environ["MONGODB_HOST"] = "0.0.0.0"
        self.addCleanup(self.remove_env, "MONGODB_HOST")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host="0.0.0.0", port=27017)

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_port_environ(self, mongo_mock):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host='localhost', port=27017)

        os.environ["MONGODB_PORT"] = "3333"
        self.addCleanup(self.remove_env, "MONGODB_PORT")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host='localhost', port=3333)

    def test_add_instance(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance(
            "xname", "plan", [{"host": "host", "port": "port",
                               "container_id": "id"}])
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        self.assertEqual(instance.endpoints[0]["container_id"],
                         result.endpoints[0]["container_id"])
        storage.remove_instance(instance)

    def test_find_instance_by_name(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance(
            "xname", "plan", [{"host": "host", "container_id": "id",
                               "port": "port"}])
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        self.assertEqual(instance.endpoints[0]["container_id"],
                         result.endpoints[0]["container_id"])
        storage.remove_instance(instance)

    def test_remove_instance(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance(
            "xname", "plan",
            [{"host": "host", "container_id": "id", "port": "port"}])
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        endpoint = instance.endpoints[0]
        self.assertEqual(endpoint["container_id"],
                         result.endpoints[0]["container_id"])
        storage.remove_instance(instance)
        length = storage.conn()['redisapi']['instances'].find(
            {"name": instance.name}).count()
        self.assertEqual(length, 0)
