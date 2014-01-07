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
        self.manager.add_instance()
        self.manager.client.build.assert_called()
