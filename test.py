# Copyright 2013 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os
import unittest

import mock


class FakeConnection(object):
    connected = False

    def connect(self):
        self.connected = True


class RedisAPITestCase(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        os.environ["REDIS_SERVER_HOST"] = "localhost"
        self.addCleanup(self.remove_env, "REDIS_SERVER_HOST")

    def test_running_without_the_REDIS_SERVER_HOST_variable(self):
        del os.environ["REDIS_SERVER_HOST"]
        with self.assertRaises(Exception) as cm:
            import redisapi
            reload(redisapi)
        exc = cm.exception
        self.assertEqual(
            (u"You must define the REDIS_SERVER_HOST environment variable.",),
            exc.args,
        )

    def test_add_instance_does_nothing(self):
        import redisapi
        app = redisapi.app.test_client()
        response = app.post("/resources")
        self.assertEqual(201, response.status_code)
        self.assertEqual("", response.data)

    def test_remove_instance_does_nothing(self):
        import redisapi
        app = redisapi.app.test_client()
        response = app.delete("/resources/myinstance")
        self.assertEqual(200, response.status_code)
        self.assertEqual("", response.data)

    def test_bind_returns_the_server_host_and_port(self):
        import redisapi
        app = redisapi.app.test_client()
        response = app.post("/resources/myinstance",
                            data={"hostname": "something.tsuru.io"})
        self.assertEqual(201, response.status_code)
        j = json.loads(response.data)
        self.assertEqual({"REDIS_HOST": "localhost", "REDIS_PORT": "6379"}, j)

    def test_bind_returns_the_REDIS_PUBLIC_HOST_when_its_defined(self):
        os.environ["REDIS_PUBLIC_HOST"] = "redis.tsuru.io"
        self.addCleanup(self.remove_env, "REDIS_PUBLIC_HOST")
        import redisapi
        app = redisapi.app.test_client()
        response = app.post("/resources/myinstance",
                            data={"hostname": "something.tsuru.io"})
        self.assertEqual(201, response.status_code)
        j = json.loads(response.data)
        want = {
            "REDIS_HOST": "redis.tsuru.io",
            "REDIS_PORT": "6379",
        }
        self.assertEqual(want, j)

    def test_bind_returns_the_REDIS_SERVER_PORT_when_its_defined(self):
        os.environ["REDIS_SERVER_PORT"] = "12345"
        self.addCleanup(self.remove_env, "REDIS_SERVER_PORT")
        import redisapi
        app = redisapi.app.test_client()
        response = app.post("/resources/myinstance",
                            data={"hostname": "something.tsuru.io"})
        self.assertEqual(201, response.status_code)
        j = json.loads(response.data)
        want = {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "12345",
        }
        self.assertEqual(want, j)

    def test_bind_returns_the_password_when_its_defined(self):
        os.environ["REDIS_SERVER_PASSWORD"] = "s3cr3t"
        self.addCleanup(self.remove_env, "REDIS_SERVER_PASSWORD")
        import redisapi
        app = redisapi.app.test_client()
        response = app.post("/resources/myinstance",
                            data={"hostname": "something.tsuru.io"})
        self.assertEqual(201, response.status_code)
        j = json.loads(response.data)
        want = {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "s3cr3t",
        }
        self.assertEqual(want, j)

    def test_unbind_does_nothing(self):
        import redisapi
        content, code = redisapi.unbind("instance", "10.10.10.10")
        self.assertEqual(200, code)
        self.assertEqual("", content)

    @mock.patch("redis.Connection")
    def test_status(self, Connection):
        f = FakeConnection()
        Connection.return_value = f
        import redisapi
        content, code = redisapi.status("myinstance")
        self.assertEqual(204, code)
        self.assertEqual("", content)
        Connection.assert_called_with(host="localhost")
        self.assertTrue(f.connected)

if __name__ == "__main__":
    unittest.main()
