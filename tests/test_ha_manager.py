# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest


class DockerHaManagerTest(unittest.TestCase):

    def test_hc(self):
        from redisapi.hc import FakeHealthCheck
        from redisapi.managers import DockerHaManager
        manager = DockerHaManager()
        self.assertIsInstance(manager.health_checker(), FakeHealthCheck)
