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
        instance = Instance(
            host=host,
            container_id=id,
            name=name,
            port=port,
        )
        self.assertEqual(instance.host, host)
        self.assertEqual(instance.container_id, id)
        self.assertEqual(instance.name, name)
        self.assertEqual(instance.port, port)

    def test_to_json(self):
        host = "host"
        id = "id"
        name = "name"
        port = "port"
        instance = Instance(
            host=host,
            container_id=id,
            name=name,
            port=port,
        )
        expected = {
            'host': host,
            'name': name,
            'port': port,
            'container_id': id,
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
        instance = Instance("host", "id", "port", "xname")
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        self.assertEqual(instance.container_id, result["container_id"])
        storage.conn()['redisapi']['instances'].remove({"name": instance.name})

    def test_find_instance_by_name(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance("host", "id", "port", "xname")
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        self.assertEqual(instance.container_id, result["container_id"])
        storage.conn()['redisapi']['instances'].remove({"name": instance.name})
