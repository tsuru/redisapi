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
from redisapi.managers import SharedManager, DockerManager, DockerHaManager


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
        os.environ["DOCKER_HOSTS"] = "[]"
        os.environ["REDIS_SERVER_HOST"] = ""
        os.environ["REDIS_IMAGE"] = ""
        manager = manager_by_plan_name("basic")
        self.assertIsInstance(manager, DockerManager)

    def test_manager_by_plan_name_plus(self):
        os.environ["SENTINEL_HOSTS"] = "[]"
        manager = manager_by_plan_name("plus")
        self.assertIsInstance(manager, DockerHaManager)

    def test_manager_by_instance(self):
        os.environ["REDIS_IMAGE"] = "redisapi"
        os.environ["DOCKER_HOSTS"] = "[]"
        os.environ["SENTINEL_HOSTS"] = "[]"
        instance = Instance(
            name='name',
            plan='plus',
            endpoints=[{"host": "host", "port": "port", "container_id": "id"}],
        )
        manager = manager_by_instance(instance)
        self.assertIsInstance(manager, DockerHaManager)

    @mock.patch("redisapi.api.manager_by_plan_name")
    @mock.patch("redisapi.storage.MongoStorage")
    def test_add_instance(self, mongo_mock, manager):
        storage_mock = mongo_mock.return_value
        fake_mock = mock.Mock()
        fake_instance = mock.Mock()
        fake_mock.add_instance.return_value = fake_instance
        manager.return_value = fake_mock

        response = self.app.post("/resources",
                                 data={"name": "name", "plan": "basic"})

        self.assertEqual(201, response.status_code)
        self.assertEqual("", response.data)
        manager.assert_called_with('basic')
        storage_mock.add_instance.assert_called_with(fake_instance)

    @mock.patch("redisapi.api.manager_by_instance")
    @mock.patch("redisapi.storage.MongoStorage")
    def test_remove_instance(self, mongo_mock, manager_mock):
        storage_mock = mongo_mock.return_value
        instance_mock = mock.Mock()
        storage_mock.find_instance_by_name.return_value = instance_mock

        response = self.app.delete("/resources/myinstance")

        self.assertEqual(200, response.status_code)
        self.assertEqual("", response.data)
        storage_mock.remove_instance.assert_called_with(instance_mock)

    def test_bind_app(self):
        storage = MongoStorage()
        instance = Instance(
            name='myinstance',
            plan='development',
            endpoints=[{"host": "host", "port": "port",
                        "container_id": "id"}],
        )
        storage.add_instance(instance)
        response = self.app.post(
            "/resources/myinstance/bind-app",
            data={"hostname": "something.tsuru.io"}
        )
        self.assertEqual(201, response.status_code)
        j = json.loads(response.data)
        endpoint = instance.endpoints[0]
        self.assertDictEqual({"REDIS_HOST": endpoint["host"],
                              "REDIS_PORT": endpoint["port"]}, j)

    def test_unbind_app(self):
        response = self.app.delete("/resources/myinstance/bind-app")
        self.assertEqual(200, response.status_code)
        self.assertEqual("", response.data)

    @mock.patch("redisapi.api.manager_by_instance")
    def test_status(self, manager_mock):
        fake_manager = mock.Mock()
        fake_manager.is_ok.return_value = False, "error"
        manager_mock.return_value = fake_manager
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
