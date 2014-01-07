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

    def test_bind(self):
        from redisapi import FakeManager
        manager = FakeManager()
        self.assertFalse(manager.binded)
        manager.bind()
        self.assertTrue(manager.binded)

    def test_unbind(self):
        from redisapi import FakeManager
        manager = FakeManager()
        self.assertFalse(manager.unbinded)
        manager.unbind()
        self.assertTrue(manager.unbinded)

    def test_remove_instance(self):
        from redisapi import FakeManager
        manager = FakeManager()
        self.assertFalse(manager.removed)
        manager.remove()
        self.assertTrue(manager.removed)
