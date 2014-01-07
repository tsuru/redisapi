# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import unittest


class RedisAPITestCase(unittest.TestCase):

    def test_add_instance(self):
        import redisapi
        app = redisapi.app.test_client()
        response = app.post("/resources")
        self.assertEqual(201, response.status_code)
        self.assertEqual("", response.data)

    def test_remove_instance(self):
        import redisapi
        app = redisapi.app.test_client()
        response = app.delete("/resources/myinstance")
        self.assertEqual(200, response.status_code)
        self.assertEqual("", response.data)

    def test_bind(self):
        import redisapi
        app = redisapi.app.test_client()
        response = app.post("/resources/myinstance",
                            data={"hostname": "something.tsuru.io"})
        self.assertEqual(201, response.status_code)
        j = json.loads(response.data)
        self.assertEqual({"REDIS_HOST": "localhost", "REDIS_PORT": "6379"}, j)

    def test_unbind(self):
        import redisapi
        content, code = redisapi.unbind("instance", "10.10.10.10")
        self.assertEqual(200, code)
        self.assertEqual("", content)

    def test_status(self):
        import redisapi
        content, code = redisapi.status("myinstance")
        self.assertEqual(204, code)
        self.assertEqual("", content)
