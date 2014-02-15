# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import mock
import os
import unittest

from redisapi.hc import FakeHealthCheck
from redisapi.managers import DockerHaManager
from redisapi.storage import Instance, MongoStorage


class DockerHaManagerTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        os.environ["REDIS_IMAGE"] = "redisapi"
        self.addCleanup(self.remove_env, "REDIS_IMAGE")
        os.environ["DOCKER_HOSTS"] = '["http://host1.com:4243", \
            "http://localhost:4243", "http://host2.com:4243"]'
        self.addCleanup(self.remove_env, "DOCKER_HOSTS")
        os.environ["SENTINEL_HOSTS"] = '["http://host1.com:4243", \
            "http://localhost:4243", "http://host2.com:4243"]'
        self.addCleanup(self.remove_env, "SENTINEL_HOSTS")
        self.manager = DockerHaManager()
        self.storage = MongoStorage()

    def test_hc(self):
        self.assertIsInstance(self.manager.health_checker(), FakeHealthCheck)

    def test_sentinel_hosts(self):
        hosts = ["http://host1.com:4243", "http://localhost:4243",
                 "http://host2.com:4243"]
        self.assertListEqual(self.manager.sentinel_hosts, hosts)

    def test_docker_hosts(self):
        hosts = ["http://host1.com:4243", "http://localhost:4243",
                 "http://host2.com:4243"]
        self.assertListEqual(self.manager.docker_hosts, hosts)

    def test_client(self):
        manager = DockerHaManager()
        client = manager.client(host="myhost")
        self.assertIn(client.base_url, "myhost")

    @mock.patch("redis.StrictRedis")
    def test_config_sentinels(self, redis_mock):
        redis_instance_mock = mock.Mock()
        redis_mock.return_value = redis_instance_mock

        master = {"host": "localhost", "port": "3333"}
        self.manager.config_sentinels("master_name", master)

        redis_mock.assert_called_with(host="host", port="port")
        redis_instance_mock.execute_command.assert_called_with(
            'sentinel set master_name parallel-syncs 1'
        )

    @mock.patch("redis.StrictRedis")
    def test_slave_of(self, redis_mock):
        redis_instance_mock = mock.Mock()
        redis_mock.return_value = redis_instance_mock
        master = {"host": "localhost", "port": "3333"}
        slave = {"host": "myhost", "port": "9999"}
        self.manager.slave_of(master, slave)
        redis_mock.assert_called_with(host=slave["host"], port=["port"])
        redis_instance_mock.slaveof(master["host"], master["port"])

    def test_add_instance(self):
        add_mock = mock.Mock()
        self.manager.health_checker = mock.Mock()
        self.manager.health_checker.return_value = add_mock
        self.manager.slave_of = mock.Mock()
        self.manager.config_sentinels = mock.Mock()
        self.manager.client = mock.Mock(base_url="http://localhost:4243")
        self.manager.client().create_container.return_value = {"Id": "12"}
        self.manager.client().inspect_container.return_value = {
            'NetworkSettings': {
                u'Ports': {
                    u'6379/tcp': [{u'HostPort': u'49154'}]}}}

        instance = self.manager.add_instance("name")

        self.manager.client().create_container.assert_called_with(
            self.manager.image_name,
            command="",
        )
        self.manager.client().start.assert_called_with(
            "12",
            port_bindings={6379: ('0.0.0.0',)}
        )
        add_mock.add.assert_called_with("localhost", u"49154")
        expected_endpoints = [
            {"container_id": "12", "host": "localhost", "port": "49154"},
            {"container_id": "12", "host": "localhost", "port": "49154"},
        ]
        self.assertEqual(instance.name, "name")
        self.assertListEqual(instance.endpoints, expected_endpoints)
        self.assertEqual(instance.plan, "basic")

        self.manager.slave_of.assert_called_with(*expected_endpoints)
        self.manager.config_sentinels.assert_called_with(
            "name", expected_endpoints[0])

    def test_remove_instance(self):
        remove_mock = mock.Mock()
        self.manager.health_checker = mock.Mock()
        self.manager.health_checker.return_value = remove_mock
        self.manager.client = mock.Mock()
        self.manager.client.return_value = mock.Mock()
        instance = Instance(
            name="name",
            plan="basic",
            endpoints=[
                {"host": "host", "port": 123, "container_id": "12"},
                {"host": "host", "port": 123, "container_id": "12"},
                {"host": "host", "port": 123, "container_id": "12"},
            ],
        )
        self.storage.add_instance(instance)

        self.manager.remove_instance(instance)

        remove_mock.remove.assert_called_with("host", 123)
        self.manager.client.assert_called_with("http://host:4243")
        self.manager.client().stop.assert_called_with(
            instance.endpoints[0]["container_id"])
        self.manager.client().remove_container.assert_called(
            instance.endpoints[0]["container_id"])
        self.storage.remove_instance(instance)
