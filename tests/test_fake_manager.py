# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import os


class FakeManagerTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        os.environ["REDIS_SERVER_HOST"] = "localhost"
        self.addCleanup(self.remove_env, "REDIS_SERVER_HOST")

    def test_add_instance(self):
        from redisapi import FakeManager
        manager = FakeManager()
        self.assertFalse(manager.instance_added)
        manager.add_instance()
        self.assertTrue(manager.instance_added)
