# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest

from redisapi.storage import Instance


class InstanceTest(unittest.TestCase):

    def test_instance(self):
        host = "host"
        id = "id"
        name = "name"
        port = "port"
        instance = Instance(
            host=host,
            container_id=id,
            name=name,
            port=port,
        )
        self.assertEqual(instance.host, host)
        self.assertEqual(instance.container_id, id)
        self.assertEqual(instance.name, name)
        self.assertEqual(instance.port, port)
