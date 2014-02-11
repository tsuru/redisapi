# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import unittest
import os
import mock

from redisapi import plans
from redisapi.api import manager_by_plan_name, manager_by_instance
from redisapi.storage import Instance, MongoStorage
from redisapi.managers import (SharedManager, DockerManager,
                               DockerHaManager, FakeManager)


class RedisAPITestCase(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        os.environ["REDIS_SERVER_HOST"] = "localhost"
        self.addCleanup(self.remove_env, "REDIS_SERVER_HOST")
        from redisapi import api
        self.app = api.app.test_client()

    def test_manager_by_plan_name_development(self):
        manager = manager_by_plan_name("development")
        self.assertIsInstance(manager, SharedManager)

    def test_manager_by_plan_name_basic(self):
        os.environ["REDIS_SERVER_HOST"] = ""
        os.environ["REDIS_IMAGE"] = ""
        manager = manager_by_plan_name("basic")
        self.assertIsInstance(manager, DockerManager)

    def test_manager_by_plan_name_plus(self):
        manager = manager_by_plan_name("plus")
        self.assertIsInstance(manager, DockerHaManager)

    def test_manager_by_instance(self):
        instance = Instance(
            host='host',
            container_id='id',
            name='name',
            port='port',
            plan='plus',
        )
        manager = manager_by_instance(instance)
        self.assertIsInstance(manager, DockerHaManager)

    def test_manager(self):
        from redisapi.managers import SharedManager
        from redisapi.api import manager
        self.assertIsInstance(manager(), SharedManager)

    def test_manager_fake_manager(self):
        os.environ["API_MANAGER"] = "fake"
        from redisapi.api import manager
        self.assertIsInstance(manager(), FakeManager)

    @mock.patch("redisapi.api.manager_by_plan_name")
    def test_add_instance(self, manager):
        manager.return_value = FakeManager()
        response = self.app.post("/resources",
                                 data={"name": "name", "plan": "basic"})
        self.assertEqual(201, response.status_code)
        self.assertEqual("", response.data)
        manager.assert_called_with('basic')

    def test_remove_instance(self):
        response = self.app.delete("/resources/myinstance")
        self.assertEqual(200, response.status_code)
        self.assertEqual("", response.data)

    def test_bind(self):
        storage = MongoStorage()
        instance = Instance(
            host='host',
            container_id='id',
            name='myinstance',
            port='port',
            plan='development',
        )
        storage.add_instance(instance)
        response = self.app.post(
            "/resources/myinstance",
            data={"hostname": "something.tsuru.io"}
        )
        self.assertEqual(201, response.status_code)
        j = json.loads(response.data)
        self.assertEqual({"REDIS_HOST": instance.host,
                          "REDIS_PORT": instance.port}, j)

    def test_unbind(self):
        from redisapi import api
        content, code = api.unbind("instance", "10.10.10.10")
        self.assertEqual(200, code)
        self.assertEqual("", content)

    def test_status(self):
        from redisapi import api
        content, code = api.status("myinstance")
        self.assertEqual(500, code)
        self.assertEqual("error", content)

    def test_plans(self):
        os.environ["REDIS_API_PLANS"] = '["development", "basic", "plus"]'
        response = self.app.get("/resources/plans")
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        expected = plans.plans
        self.assertListEqual(expected, data)
