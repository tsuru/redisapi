# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import os

from redisapi import hc


class FakeHCTest(unittest.TestCase):

    def setUp(self):
        from redisapi.hc import FakeHealthCheck
        self.hc = FakeHealthCheck()

    def test_add(self):
        self.assertFalse(self.hc.added)
        self.hc.add(host="localhost", port=8080)
        self.assertTrue(self.hc.added)

    def test_remove(self):
        self.assertFalse(self.hc.removed)
        self.hc.remove(host="localhost", port=8080)
        self.assertTrue(self.hc.removed)


class ZabbixHCTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    @mock.patch("pyzabbix.ZabbixAPI")
    def setUp(self, zabbix_mock):
        zapi_mock = mock.Mock()
        zabbix_mock.return_value = zapi_mock
        from redisapi.hc import ZabbixHealthCheck
        self.hc = ZabbixHealthCheck()
        zabbix_mock.assert_called_with('')
        zapi_mock.login.assert_called_with('', '')

    def tearDown(self):
        self.hc.items.remove()

    def test_add(self):
        self.hc.zapi.item.create.return_value = {"itemids": ["xpto"]}
        self.hc.zapi.trigger.create.return_value = {"itemids": ["apto"]}

        self.hc.add(host="localhost", port=8080)

        item_key = "net.tcp.service[telnet,localhost,8080]"
        self.hc.zapi.item.create.assert_called_with(
            name="redis healthcheck for localhost:8080",
            key_=item_key,
            delay=60,
            hostid="",
            interfaceid="",
            type=3,
            value_type=3,
        )
        self.hc.zapi.trigger.create.assert_called_with(
            description="trigger hc for redis localhost:8080",
            expression="{{Zabbix Server:{}.last()}}=1".format(item_key),
            priority=5,
        )

        item = self.hc.items.find_one({"host": "localhost", "port": 8080})
        self.assertEqual(item["host"], "localhost")
        self.assertEqual(item["port"], 8080)
        self.assertEqual(item["item"], "xpto")
        self.assertEqual(item["trigger"], "apto")

    def test_delete(self):
        item = {
            "host": "localhost",
            "port": 8080,
            "trigger": 43,
            "item": 42,
        }
        self.hc.items.insert(item)

        self.hc.delete(host="localhost", port=8080)

        self.hc.zapi.trigger.delete.assert_called_with([43])
        self.hc.zapi.item.delete.assert_called_with([42])
        lenght = self.hc.items.find({
            "host": "localhost",
            "port": 8080}).count()
        self.assertEqual(lenght, 0)

    @mock.patch("pymongo.MongoClient")
    @mock.patch("pyzabbix.ZabbixAPI")
    def test_mongodb_host_environ(self, zapi, mongo_mock):
        from redisapi.hc import ZabbixHealthCheck
        ZabbixHealthCheck()
        mongo_mock.assert_called_with(host="localhost", port=27017)

        os.environ["MONGODB_HOST"] = "0.0.0.0"
        self.addCleanup(self.remove_env, "MONGODB_HOST")
        from redisapi.hc import ZabbixHealthCheck
        ZabbixHealthCheck()
        mongo_mock.assert_called_with(host="0.0.0.0", port=27017)

    @mock.patch("pymongo.MongoClient")
    @mock.patch("pyzabbix.ZabbixAPI")
    def test_mongodb_port_environ(self, zapi, mongo_mock):
        from redisapi.hc import ZabbixHealthCheck
        ZabbixHealthCheck()
        mongo_mock.assert_called_with(host='localhost', port=27017)

        os.environ["MONGODB_PORT"] = "3333"
        self.addCleanup(self.remove_env, "MONGODB_PORT")
        from redisapi.hc import ZabbixHealthCheck
        ZabbixHealthCheck()
        mongo_mock.assert_called_with(host='localhost', port=3333)


class HCTest(unittest.TestCase):

    def test_zabbix(self):
        self.assertEqual(hc.health_checkers['zabbix'], hc.ZabbixHealthCheck)
        self.assertEqual(hc.health_checkers['fake'], hc.FakeHealthCheck)
