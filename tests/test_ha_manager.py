# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import unittest

from redisapi.hc import FakeHealthCheck
from redisapi.managers import DockerHaManager


class DockerHaManagerTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        os.environ["DOCKER_HOSTS"] = '["http://host1.com:4243", \
            "http://localhost:4243"]'
        self.addCleanup(self.remove_env, "DOCKER_HOSTS")
        self.manager = DockerHaManager()

    def test_hc(self):
        self.assertIsInstance(self.manager.health_checker(), FakeHealthCheck)

    def test_client(self):
        hosts = ["http://host1.com:4243", "http://localhost:4243"]
        self.assertListEqual(self.manager.docker_hosts, hosts)
