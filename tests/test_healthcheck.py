# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest


class HealthCheckManagerTest(unittest.TestCase):

    def setUp(self):
        from redisapi.hc import FakeHealthCheck
        self.hc = FakeHealthCheck()

    def test_add(self):
        self.assertFalse(self.hc.added)
        self.hc.add(host="localhost", port=8080)
        self.assertTrue(self.hc.added)
