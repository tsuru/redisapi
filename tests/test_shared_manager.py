# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import os
import mock

from redis import exceptions
from redisapi.storage import Instance


class FakeConnection(object):
    connected = False

    def connect(self):
        self.connected = True


class FailingFakeConnection(object):

    def connect(self):
        raise exceptions.ConnectionError(
            "Error 61 connecting localhost:6379. Connection refused.",
        )


class SharedManagerTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        os.environ["REDIS_SERVER_HOST"] = "localhost"
        self.addCleanup(self.remove_env, "REDIS_SERVER_HOST")
        from redisapi.managers import SharedManager
        self.manager = SharedManager()

    def test_bind_returns_the_server_host_and_port(self):
        instance = Instance(
            name='ble',
            host='localhost',
            port='6379',
            plan='development',
            container_id='',
        )
        envs = self.manager.bind(instance)
        self.assertEqual(
            {"REDIS_HOST": "localhost", "REDIS_PORT": "6379"},
            envs
        )

    def test_add_instance(self):
        instance = self.manager.add_instance("ble")
        self.assertEqual(instance.name, 'ble')
        self.assertEqual(instance.host, 'localhost')
        self.assertEqual(instance.port, '6379')
        self.assertEqual(instance.plan, 'development')
        self.assertEqual(instance.container_id, '')

    def test_add_instance_returns_the_REDIS_PUBLIC_HOST_when_its_defined(self):
        os.environ["REDIS_PUBLIC_HOST"] = "redis.tsuru.io"
        self.addCleanup(self.remove_env, "REDIS_PUBLIC_HOST")
        instance = self.manager.add_instance('ble')
        self.assertEqual(instance.port, "6379")
        self.assertEqual(instance.host, "redis.tsuru.io")

    def test_bind_returns_the_REDIS_SERVER_PORT_when_its_defined(self):
        instance = Instance(
            name='ble',
            host='localhost',
            port='12345',
            plan='development',
            container_id='',
        )
        envs = self.manager.bind(instance)
        want = {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "12345",
        }
        self.assertEqual(want, envs)

    @mock.patch("redis.Connection")
    def test_is_ok(self, Connection):
        f = FakeConnection()
        Connection.return_value = f
        ok, msg = self.manager.is_ok()
        self.assertTrue(ok)
        self.assertEqual("", msg)
        Connection.assert_called_with(host="localhost")
        self.assertTrue(f.connected)

    @mock.patch("redis.Connection")
    def test_is_ok_unavailable_server(self, Connection):
        f = FailingFakeConnection()
        Connection.return_value = f
        ok, msg = self.manager.is_ok()
        self.assertFalse(ok)
        want_msg = "Error 61 connecting localhost:6379. Connection refused."
        self.assertEqual(want_msg, msg)

    @mock.patch("redis.Connection")
    def test_is_ok_with_password(self, Connection):
        os.environ["REDIS_SERVER_PASSWORD"] = "s3cr3t"
        self.addCleanup(self.remove_env, "REDIS_SERVER_PASSWORD")
        f = FakeConnection()
        Connection.return_value = f
        ok, msg = self.manager.is_ok()
        self.assertTrue(ok)
        Connection.assert_called_with(host="localhost", password="s3cr3t")

    def test_running_without_the_REDIS_SERVER_HOST_variable(self):
        del os.environ["REDIS_SERVER_HOST"]
        with self.assertRaises(Exception) as cm:
            from redisapi.managers import SharedManager
            SharedManager()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the REDIS_SERVER_HOST environment variable.",),
            exc.args,
        )
