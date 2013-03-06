# Copyright 2013 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import unittest


class RedisAPITestCase(unittest.TestCase):

    def setUp(self):
        os.environ["REDIS_SERVER_HOST"] = "localhost"

        def remove(x):
            del x
        self.addCleanup(remove, os.environ["REDIS_SERVER_HOST"])

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

if __name__ == "__main__":
    unittest.main()
