# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import redis
import docker


def get_value(key):
    try:
        value = os.environ[key]
    except KeyError:
        msg = u"You must define the {} " \
              "environment variable.".format(key)
        raise Exception(msg)
    return value


class DockerManager(object):
    def __init__(self):
        self.server = get_value("REDIS_SERVER_HOST")
        self.image_name = get_value("REDIS_IMAGE")

        self.client = docker.Client(
            base_url='unix://var/run/docker.sock'
        )

        self.instances = self.mongo()['redisapi']['instances']

    def mongo(self):
        mongodb_host = os.environ.get("MONGODB_HOST", "localhost")
        mongodb_port = int(os.environ.get("MONGODB_PORT", 27017))

        from pymongo import MongoClient
        return MongoClient(host=mongodb_host, port=mongodb_port)

    def add_instance(self, instance_name):
        output = self.client.create_container(self.image_name, command="")
        self.client.start(output["Id"], port_bindings={6379: ('0.0.0.0',)})
        container = self.client.inspect_container(output["Id"])
        port = container['NetworkSettings']['Ports']['6379/tcp'][0]['HostPort']
        instance = {
            'name': instance_name,
            'container_id': output["Id"],
            'host': self.server,
            'port': port,
        }
        self.instances.insert(instance)

    def bind(self, name):
        instance = self.instances.find_one({"name": name})
        return {
            "REDIS_HOST": instance["host"],
            "REDIS_PORT": instance["port"],
        }

    def unbind(self):
        pass

    def remove_instance(self, name):
        instance = self.instances.find_one({"name": name})
        self.client.stop(instance["container_id"])
        self.client.remove_container(instance["container_id"])
        self.instances.remove({"name": "name"})

    def is_ok(self):
        pass


class FakeManager(object):
    instance_added = False
    binded = False
    unbinded = False
    removed = False
    ok = False
    msg = "error"

    def add_instance(self):
        self.instance_added = True

    def bind(self):
        self.binded = True

    def unbind(self):
        self.unbinded = True

    def remove_instance(self):
        self.removed = True

    def is_ok(self):
        return self.ok, self.msg


class RedisManager(object):
    def __init__(self):
        self.server = get_value("REDIS_SERVER_HOST")

    def add_instance(self):
        pass

    def bind(self):
        host = os.environ.get("REDIS_PUBLIC_HOST", self.server)
        port = os.environ.get("REDIS_SERVER_PORT", "6379")
        result = {
            "REDIS_HOST": host,
            "REDIS_PORT": port,
        }
        pswd = os.environ.get("REDIS_SERVER_PASSWORD")
        if pswd:
            result["REDIS_PASSWORD"] = pswd
        return result

    def unbind(self):
        pass

    def remove_instance(self):
        pass

    def is_ok(self):
        passwd = os.environ.get("REDIS_SERVER_PASSWORD")
        kw = {"host": self.server}
        if passwd:
            kw["password"] = passwd
        try:
            conn = redis.Connection(**kw)
            conn.connect()
        except Exception as e:
            return False, str(e)
        return True, ""


managers = {
    'shared': RedisManager,
    'fake': FakeManager,
    'docker': DockerManager,
}
