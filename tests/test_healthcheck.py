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
        url = "http://zbx.com"
        user = "user"
        password = "pass"
        os.environ["ZABBIX_URL"] = url
        os.environ["ZABBIX_USER"] = user
        os.environ["ZABBIX_PASSWORD"] = password
        os.environ["ZABBIX_HOST"] = "1"
        os.environ["ZABBIX_INTERFACE"] = "1"
        self.addCleanup(self.remove_env, "REDIS_SERVER_HOST")
        zapi_mock = mock.Mock()
        zabbix_mock.return_value = zapi_mock
        from redisapi.hc import ZabbixHealthCheck
        self.hc = ZabbixHealthCheck()
        zabbix_mock.assert_called_with(url)
        zapi_mock.login.assert_called_with(user, password)

    def tearDown(self):
        self.hc.items.remove()

    def test_add(self):
        self.hc.zapi.item.create.return_value = {"itemids": ["xpto"]}
        self.hc.zapi.trigger.create.return_value = {"triggerids": ["apto"]}

        self.hc.add(host="localhost", port=8080)

        item_key = "net.tcp.service[telnet,localhost,8080]"
        self.hc.zapi.item.create.assert_called_with(
            name="redis healthcheck for localhost:8080",
            key_=item_key,
            delay=60,
            hostid="1",
            interfaceid="1",
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

    def test_remove(self):
        item = {
            "host": "localhost",
            "port": 8080,
            "trigger": 43,
            "item": 42,
        }
        self.hc.items.insert(item)

        self.hc.remove(host="localhost", port=8080)

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

    def test_running_without_the_ZABBIX_URL_variable(self):
        del os.environ["ZABBIX_URL"]
        with self.assertRaises(Exception) as cm:
            from redisapi.hc import ZabbixHealthCheck
            ZabbixHealthCheck()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the ZABBIX_URL environment variable.",),
            exc.args,
        )

    def test_running_without_the_ZABBIX_USER_variable(self):
        del os.environ["ZABBIX_USER"]
        with self.assertRaises(Exception) as cm:
            from redisapi.hc import ZabbixHealthCheck
            ZabbixHealthCheck()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the ZABBIX_USER environment variable.",),
            exc.args,
        )

    def test_running_without_the_ZABBIX_PASSWORD_variable(self):
        del os.environ["ZABBIX_PASSWORD"]
        with self.assertRaises(Exception) as cm:
            from redisapi.hc import ZabbixHealthCheck
            ZabbixHealthCheck()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the ZABBIX_PASSWORD environment variable.",),
            exc.args,
        )

    def test_running_without_the_ZABBIX_HOST_variable(self):
        del os.environ["ZABBIX_HOST"]
        with self.assertRaises(Exception) as cm:
            from redisapi.hc import ZabbixHealthCheck
            ZabbixHealthCheck()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the ZABBIX_HOST environment variable.",),
            exc.args,
        )

    def test_running_without_the_ZABBIX_INTERFACE_variable(self):
        del os.environ["ZABBIX_INTERFACE"]
        with self.assertRaises(Exception) as cm:
            from redisapi.hc import ZabbixHealthCheck
            ZabbixHealthCheck()
        exc = cm.exception
        self.assertEqual(
            (u"You must define the ZABBIX_INTERFACE environment variable.",),
            exc.args,
        )


class HCTest(unittest.TestCase):

    def test_zabbix(self):
        self.assertEqual(hc.health_checkers['zabbix'], hc.ZabbixHealthCheck)
        self.assertEqual(hc.health_checkers['fake'], hc.FakeHealthCheck)
