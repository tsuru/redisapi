# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import os

from redisapi.storage import Instance


class DockerManagerTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        os.environ["REDIS_SERVER_HOST"] = "localhost"
        self.addCleanup(self.remove_env, "REDIS_SERVER_HOST")
        os.environ["REDIS_IMAGE"] = "redisapi"
        self.addCleanup(self.remove_env, "REDIS_IMAGE")
        os.environ["DOCKER_HOSTS"] = '["http://host1.com:4243", \
            "http://localhost:4243"]'
        self.addCleanup(self.remove_env, "DOCKER_HOSTS")
        from redisapi.managers import DockerManager
        self.manager = DockerManager()
        client_mock = mock.Mock()
        client_mock.return_value = mock.Mock()
        self.manager.client = client_mock
        self.manager.health_checker = mock.Mock()

    def tearDown(self):
        self.manager.storage.conn()['redisapi']['instances'].remove()

    def test_client(self):
        os.environ["DOCKER_HOSTS"] = '["http://host1.com:4243", \
            "http://localhost:4243"]'
        self.addCleanup(self.remove_env, "DOCKER_HOSTS")
        from redisapi.managers import DockerManager
        manager = DockerManager()
        client = manager.client()
        hosts = ["http://host1.com:4243", "http://localhost:4243"]
        self.assertIn(client.base_url, hosts)

    def test_extract_hostname(self):
        from redisapi.managers import DockerManager
        manager = DockerManager()
        url = manager.extract_hostname("http://host.com:4243")
        self.assertEqual(url, "host.com")

    def test_client_with_value(self):
        from redisapi.managers import DockerManager
        manager = DockerManager()
        host = "http://myhost.com"
        client = manager.client(host=host)
        self.assertEqual(client.base_url, host)

    def test_hc(self):
        from redisapi.hc import FakeHealthCheck
        from redisapi.managers import DockerManager
        manager = DockerManager()
        self.assertIsInstance(manager.health_checker(), FakeHealthCheck)

    def test_docker_hosts(self):
        hosts = ["http://host1.com:4243", "http://localhost:4243"]
        self.assertListEqual(self.manager.docker_hosts, hosts)

    @mock.patch("pyzabbix.ZabbixAPI")
    def test_hc_zabbix(self, zabix_mock):
        os.environ["ZABBIX_URL"] = "url"
        os.environ["ZABBIX_USER"] = "url"
        os.environ["ZABBIX_PASSWORD"] = "url"
        os.environ["HEALTH_CHECKER"] = "zabbix"
        self.addCleanup(self.remove_env, "HEALTH_CHECKER")
        os.environ["ZABBIX_HOST"] = "2"
        os.environ["ZABBIX_INTERFACE"] = "1"
        from redisapi.hc import ZabbixHealthCheck
        from redisapi.managers import DockerManager
        manager = DockerManager()
        self.assertIsInstance(manager.health_checker(), ZabbixHealthCheck)

    def test_add_instance(self):
        add_mock = mock.Mock()
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
        self.assertEqual(instance.name, "name")
        self.assertEqual(instance.container_id, "12")
        self.assertEqual(instance.host, "localhost")
        self.assertEqual(instance.port, u"49154")
        self.assertEqual(instance.plan, "basic")

    def test_remove_instance(self):
        remove_mock = mock.Mock()
        self.manager.health_checker.return_value = remove_mock
        instance = Instance(
            name="name",
            container_id="12",
            port=123,
            host="host",
            plan="basic",
        )
        self.manager.storage.add_instance(instance)

        self.manager.remove_instance(instance)
        remove_mock.remove.assert_called_with("localhost", 123)
        self.manager.client().stop.assert_called_with(instance.container_id)
        self.manager.client().remove_container.assert_called(
            instance.container_id)
        self.manager.storage.remove_instance(instance)

    def test_bind(self):
        instance = Instance(
            name="name",
            container_id="12",
            host='localhost',
            port='4242',
            plan='basic',
        )
        result = self.manager.bind(instance)
        self.assertEqual(result['REDIS_HOST'], instance.host)
        self.assertEqual(result['REDIS_PORT'], instance.port)

    def test_running_without_the_REDIS_SERVER_HOST_variable(self):
        del os.environ["REDIS_SERVER_HOST"]
        with self.assertRaises(Exception) as cm:
            from redisapi.managers import DockerManager
            DockerManager()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the REDIS_SERVER_HOST environment variable.",),
            exc.args,
        )

    def test_running_without_the_REDIS_IMAGE_variable(self):
        del os.environ["REDIS_IMAGE"]
        with self.assertRaises(Exception) as cm:
            from redisapi.managers import DockerManager
            DockerManager()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the REDIS_IMAGE environment variable.",),
            exc.args,
        )
