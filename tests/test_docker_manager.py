# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock


class FakeManagerTest(unittest.TestCase):

    def setUp(self):
        from managers import DockerManager
        self.manager = DockerManager()
        self.manager.client = mock.Mock()

    def test_add_instance(self):
        self.manager.client.build.return_value = "12", ""
        self.manager.add_instance("name")
        self.manager.client.build.assert_called()
        instance = self.manager.instances.find_one({"name": "name"})
        self.assertEqual(instance["name"], "name")
        self.assertEqual(instance["container_id"], "12")

    def test_remove_instance(self):
        self.manager.remove_instance()
        self.manager.client.stop.assert_called()
        self.manager.client.remove_container.assert_called()
