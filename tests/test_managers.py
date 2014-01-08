# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest

from managers import DockerManager, RedisManager, FakeManager, managers


class ManagersTest(unittest.TestCase):

    def test_docker(self):
        self.assertEqual(managers['docker'], DockerManager)

    def test_fake(self):
        self.assertEqual(managers['fake'], FakeManager)

    def test_shared(self):
        self.assertEqual(managers['shared'], RedisManager)
