# Copyright 2014 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import mock
import os
import unittest
import json

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
        client = manager.client(host="myhost:4243")
        self.assertEqual("http://myhost:4243", client.base_url)

    @mock.patch("redis.StrictRedis")
    def test_config_sentinels(self, redis_mock):
        master = {"host": "localhost", "port": "3333"}
        self.manager.config_sentinels("master_name", master)

        calls = []
        sentinels = [
            {"host": u"host1.com", "port": u"4243"},
            {"host": u"localhost", "port": u"4243"},
            {"host": u"host2.com", "port": u"4243"},
        ]
        for sentinel in sentinels:
            host, port = sentinel["host"], sentinel["port"]
            sentinel_calls = [
                mock.call(host=host, port=port),
                mock.call().sentinel(
                    'monitor', 'master_name', 'localhost', '3333', '1'),
                mock.call().sentinel(
                    'set', 'master_name', 'down-after-milliseconds', '5000'),
                mock.call().sentinel(
                    'set', 'master_name', 'failover-timeout', '60000'),
                mock.call().sentinel(
                    'set', 'master_name', 'parallel-syncs', '1'),
            ]
            calls.extend(sentinel_calls)

        redis_mock.assert_has_calls(calls)

    @mock.patch("redis.StrictRedis")
    def test_slave_of(self, redis_mock):
        redis_instance_mock = mock.Mock()
        redis_mock.return_value = redis_instance_mock
        master = {"host": "localhost", "port": "3333"}
        slave = {"host": "myhost", "port": "9999"}
        self.manager.slave_of(master, slave)
        redis_mock.assert_called_with(
            host=str(slave["host"]), port=str(slave["port"]))
        redis_instance_mock.slaveof.assert_called_with(
            master["host"], master["port"])

    def test_add_instance(self):
        add_mock = mock.Mock()
        self.manager.health_checker = mock.Mock()
        self.manager.health_checker.return_value = add_mock
        self.manager.slave_of = mock.Mock()
        self.manager.get_port_by_host = mock.Mock()
        self.manager.get_port_by_host.return_value = 49153
        self.manager.config_sentinels = mock.Mock()
        client_mock = mock.Mock()
        client_mock.return_value = mock.Mock(base_url="http://localhost:4243")
        self.manager.client = client_mock
        self.manager.client().create_container.return_value = {"Id": "12"}
        self.manager.client().inspect_container.return_value = {
            'NetworkSettings': {
                u'Ports': {
                    u'6379/tcp': [{u'HostPort': u'49154'}]}}}

        instance = self.manager.add_instance("name")

        self.manager.get_port_by_host.assert_called_with("localhost")

        self.manager.client().create_container.assert_called_with(
            self.manager.image_name,
            command="",
            environment={'REDIS_PORT': 49153},
            ports=[49153]
        )
        self.manager.client().start.assert_called_with(
            "12",
            port_bindings={49153: ('0.0.0.0', 49153)}
        )
        add_mock.add.assert_called_with("localhost", 49153)
        expected_endpoints = [
            {"container_id": "12", "host": "localhost", "port": 49153},
            {"container_id": "12", "host": "localhost", "port": 49153},
        ]
        self.assertEqual(instance.name, "name")
        self.assertListEqual(instance.endpoints, expected_endpoints)
        self.assertEqual(instance.plan, "plus")

        self.manager.slave_of.assert_called_with(*expected_endpoints)
        self.manager.config_sentinels.assert_called_with(
            "name", expected_endpoints[0])

    def test_remove_instance(self):
        remove_mock = mock.Mock()
        self.manager.remove_from_sentinel = mock.Mock()
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
        self.manager.remove_from_sentinel.assert_called_with(
            instance.name)

    @mock.patch("redis.StrictRedis")
    def test_remove_from_sentinel(self, redis_mock):
        self.manager.remove_from_sentinel("master_name")

        calls = []
        sentinels = [
            {"host": u"host1.com", "port": u"4243"},
            {"host": u"localhost", "port": u"4243"},
            {"host": u"host2.com", "port": u"4243"},
        ]
        for sentinel in sentinels:
            host, port = sentinel["host"], sentinel["port"]
            sentinel_calls = [
                mock.call(host=host, port=port),
                mock.call().sentinel(
                    'remove', 'master_name'),
            ]
            calls.extend(sentinel_calls)

        redis_mock.assert_has_calls(calls)

    def test_bind(self):
        instance = Instance(
            name="name",
            plan='basic',
            endpoints=[
                {"host": "localhost", "port": "4242", "container_id": "12"},
                {"host": "host.com", "port": "422", "container_id": "12"},
            ],
        )
        result = self.manager.bind(instance)
        expected_redis = json.dumps(['localhost:4242', 'host.com:422'])
        expected_sentinels = json.dumps([
            u'http://host1.com:4243',
            u'http://localhost:4243',
            u'http://host2.com:4243'
        ])
        self.assertEqual(result['REDIS_HOSTS'], expected_redis)
        self.assertEqual(result['SENTINEL_HOSTS'], expected_sentinels)
        self.assertEqual(result['REDIS_MASTER'], instance.name)

    def test_grant(self):
        instance = Instance(
            name="name",
            plan='basic',
            endpoints=[
                {"host": "localhost", "port": "4242", "container_id": "12"},
                {"host": "host.com", "port": "422", "container_id": "12"},
            ],
        )
        self.manager.grant(instance, "10.0.0.1")
        self.manager.grant(instance, "10.0.0.2")
        access_mngr = self.manager.access_manager
        self.assertEqual(["10.0.0.1", "10.0.0.2"], access_mngr.permits[instance.name])

    def test_revoke(self):
        instance = Instance(
            name="name",
            plan='basic',
            endpoints=[
                {"host": "localhost", "port": "4242", "container_id": "12"},
                {"host": "host.com", "port": "422", "container_id": "12"},
            ],
        )
        self.manager.grant(instance, "10.0.0.1")
        self.manager.grant(instance, "10.0.0.2")
        access_mngr = self.manager.access_manager
        self.manager.revoke(instance, "10.0.0.1")
        self.assertEqual(["10.0.0.2"], access_mngr.permits[instance.name])

    def test_port_range_start(self):
        self.assertEqual(49153, self.manager.port_range_start)

    def test_get_port(self):
        self.assertEqual(49153, self.manager.get_port_by_host("newhost"))

    def test_get_port_host_with_containers(self):
        instance = Instance(
            name="name",
            plan="basic",
            endpoints=[{"host": "newhost", "port": 49153,
                        "container_id": "12"}],
        )
        self.storage.add_instance(instance)
        self.assertEqual(49154, self.manager.get_port_by_host("newhost"))
