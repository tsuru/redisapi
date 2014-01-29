# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os


def get_value(key):
    try:
        value = os.environ[key]
    except KeyError:
        msg = u"You must define the {} " \
              "environment variable.".format(key)
        raise Exception(msg)
    return value


class FakeHealthCheck(object):
    added = False
    removed = False

    def add(self, host, port):
        self.added = True

    def remove(self, host, port):
        self.removed = True


class ZabbixHealthCheck(object):
    def __init__(self):
        url = get_value("ZABBIX_URL")
        user = get_value("ZABBIX_USER")
        password = get_value("ZABBIX_PASSWORD")
        self.host_id = get_value("ZABBIX_HOST")
        self.interface_id = get_value("ZABBIX_INTERFACE")
        from pyzabbix import ZabbixAPI
        self.zapi = ZabbixAPI(url)
        self.zapi.login(user, password)

        self.items = self.mongo()['redisapi']['zabbix']

    def mongo(self):
        mongodb_host = os.environ.get("MONGODB_HOST", "localhost")
        mongodb_port = int(os.environ.get("MONGODB_PORT", 27017))

        from pymongo import MongoClient
        return MongoClient(host=mongodb_host, port=mongodb_port)

    def add(self, host, port):
        item_key = "net.tcp.service[telnet,{},{}]".format(host, port)
        item_result = self.zapi.item.create(
            name="redis healthcheck for {}:{}".format(host, port),
            key_=item_key,
            delay=60,
            hostid=self.host_id,
            interfaceid=self.interface_id,
            type=3,
            value_type=3,
        )
        trigger_result = self.zapi.trigger.create(
            description="trigger hc for redis {}:{}".format(host, port),
            expression="{{Zabbix Server:{}.last()}}=1".format(item_key),
            priority=5,
        )
        item = {
            'host': host,
            'port': port,
            'item': item_result['itemids'][0],
            'trigger': trigger_result['triggerids'][0],
        }
        self.items.insert(item)

    def remove(self, host, port):
        item = self.items.find_one({"host": host, "port": port})
        self.zapi.trigger.delete([item["trigger"]])
        self.zapi.item.delete([item["item"]])
        self.items.remove({"host": host, "port": port})


health_checkers = {
    'fake': FakeHealthCheck,
    'zabbix':  ZabbixHealthCheck,
}
