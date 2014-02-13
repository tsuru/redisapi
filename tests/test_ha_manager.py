# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import mock
import os
import unittest

from redisapi.hc import FakeHealthCheck
from redisapi.managers import DockerHaManager


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
        self.manager = DockerHaManager()

    def test_hc(self):
        self.assertIsInstance(self.manager.health_checker(), FakeHealthCheck)

    def test_docker_hosts(self):
        hosts = ["http://host1.com:4243", "http://localhost:4243",
                 "http://host2.com:4243"]
        self.assertListEqual(self.manager.docker_hosts, hosts)

    def test_client(self):
        manager = DockerHaManager()
        client = manager.client(host="myhost")
        self.assertIn(client.base_url, "myhost")

    def test_add_instance(self):
        add_mock = mock.Mock()
        self.manager.health_checker = mock.Mock()
        self.manager.health_checker.return_value = add_mock
        self.manager.client = mock.Mock(base_url="http://localhost:4243")
        self.manager.client().create_container.return_value = {"Id": "12"}
        self.manager.client().inspect_container.return_value = {
            'NetworkSettings': {
                u'Ports': {u'6379/tcp': [{u'HostPort': u'49154'}]}}}

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
            {"container_id": "12", "host": "localhost", "port": "49154"},
        ]
        self.assertEqual(instance.name, "name")
        self.assertListEqual(instance.endpoints, expected_endpoints)
        self.assertEqual(instance.plan, "basic")
