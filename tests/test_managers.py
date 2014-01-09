# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest

from redisapi import managers


class ManagersTest(unittest.TestCase):

    def test_docker(self):
        self.assertEqual(managers.managers['docker'], managers.DockerManager)

    def test_fake(self):
        self.assertEqual(managers.managers['fake'], managers.FakeManager)

    def test_shared(self):
        self.assertEqual(managers.managers['shared'], managers.RedisManager)
