# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import json
import redis
import docker
import random

from urlparse import urlparse
from hc import health_checkers
from utils import get_value
from storage import Instance, MongoStorage


class DockerBase(object):

    def __init__(self):
        self.image_name = get_value("REDIS_IMAGE")
        docker_hosts = get_value("DOCKER_HOSTS")
        sentinel_hosts = get_value("SENTINEL_HOSTS")
        self.sentinel_hosts = json.loads(sentinel_hosts)
        self.docker_hosts = json.loads(docker_hosts)
        self.port_range_start = 49153

    def get_port_by_host(self, host):
        storage = MongoStorage()
        instances = storage.find_instances_by_host(host)
        if instances:
            ports = []
            for instance in instances:
                for endpoint in instance.endpoints:
                    ports.append(int(endpoint["port"]))
            return max(ports) + 1
        return self.port_range_start

    def config_sentinels(self, master_name, master):
        for sentinel in self.sentinel_hosts:
            host, port = sentinel.replace("http://", "").split(":")
            r = redis.StrictRedis(host=str(host), port=str(port))
            commands = [
                ["monitor", master_name, master["host"], master["port"], '1'],
                ["set", master_name, "down-after-milliseconds", "5000"],
                ["set", master_name, "failover-timeout", "60000"],
                ["set", master_name, "parallel-syncs", "1"],
            ]
            for command in commands:
                r.sentinel(*command)

    def remove_from_sentinel(self, master_name):
        for sentinel in self.sentinel_hosts:
            host, port = sentinel.replace("http://", "").split(":")
            r = redis.StrictRedis(host=str(host), port=str(port))
            r.sentinel('remove', master_name)

    def health_checker(self):
        hc_name = os.environ.get("HEALTH_CHECKER", "fake")
        return health_checkers[hc_name]()

    def extract_hostname(self, url):
        return urlparse(url).hostname

    def docker_url_from_hostname(self, hostname):
        return "http://{}:4243".format(hostname)

    def client(self, host):
        return docker.Client(base_url=host)

    def bind(self, instance):
        redis_hosts = []

        for endpoint in instance.endpoints:
            redis_hosts.append("{}:{}".format(
                endpoint["host"], endpoint["port"]))

        return {
            "SENTINEL_HOSTS": json.dumps(self.sentinel_hosts),
            "REDIS_HOSTS": json.dumps(redis_hosts),
            "REDIS_MASTER": instance.name,
        }

    def unbind(self):
        pass

    def is_ok(self):
        pass


class DockerHaManager(DockerBase):

    def start_redis_container(self, name, host, slave_of=None):
        client = self.client(host)
        port = self.get_port_by_host(host)
        output = client.create_container(
            self.image_name,
            command="",
            ports=[port],
            environment={"REDIS_PORT": port},
        )
        client.start(output["Id"], port_bindings={port: ('0.0.0.0', port)})
        host = self.extract_hostname(client.base_url)
        self.health_checker().add(host, port)
        endpoint = {"host": host, "port": port, "container_id": output["Id"]}
        if slave_of:
            self.slave_of(slave_of, endpoint)
        else:
            self.config_sentinels(name, endpoint)
        return endpoint

    def slave_of(self, master, slave):
        r = redis.StrictRedis(host=str(slave["host"]), port=str(slave["port"]))
        r.slaveof(master["host"], master["port"])

    def add_instance(self, instance_name):
        hosts = self.docker_hosts[:]
        random.shuffle(hosts)
        endpoints = []

        host = hosts.pop()
        endpoint = self.start_redis_container(instance_name, host)
        endpoints.append(endpoint)

        host = hosts.pop()
        endpoint = self.start_redis_container(
            instance_name, host, slave_of=endpoint)
        endpoints.append(endpoint)

        return Instance(
            name=instance_name,
            plan='plus',
            endpoints=endpoints,
        )

    def remove_instance(self, instance):
        for endpoint in instance.endpoints:
            self.health_checker().remove(endpoint["host"], endpoint["port"])
            url = self.docker_url_from_hostname(endpoint["host"])
            client = self.client(url)
            client.stop(endpoint["container_id"])
            client.remove_container(endpoint["container_id"])

        self.remove_from_sentinel(instance.name)


class DockerManager(DockerBase):

    def client(self, host=None):
        if not host:
            host = random.choice(self.docker_hosts)
        return super(DockerManager, self).client(host)

    def add_instance(self, instance_name):
        client = self.client()
        host = self.extract_hostname(client.base_url)
        port = self.get_port_by_host(host)
        output = client.create_container(
            self.image_name,
            command="",
            ports=[port],
            environment={"REDIS_PORT": port},
        )
        client.start(output["Id"], port_bindings={port: ('0.0.0.0', port)})
        endpoint = {"host": host, "port": port, "container_id": output["Id"]}
        instance = Instance(
            name=instance_name,
            plan='basic',
            endpoints=[endpoint],
        )
        self.health_checker().add(host, port)
        self.config_sentinels(instance_name, endpoint)
        return instance

    def bind(self, instance):
        envs = super(DockerManager, self).bind(instance)
        envs.update({
            "REDIS_HOST": instance.endpoints[0]["host"],
            "REDIS_PORT": str(instance.endpoints[0]["port"]),
            })
        return envs

    def remove_instance(self, instance):
        endpoint = instance.endpoints[0]
        self.health_checker().remove(endpoint["host"], endpoint["port"])
        url = self.docker_url_from_hostname(endpoint["host"])
        client = self.client(url)
        client.stop(endpoint["container_id"])
        client.remove_container(endpoint["container_id"])
        self.remove_from_sentinel(instance.name)


class FakeManager(object):
    instance_added = False
    binded = False
    unbinded = False
    removed = False
    ok = False
    msg = "error"

    def add_instance(self, name):
        self.instance_added = True

    def bind(self, instance):
        self.binded = True

    def unbind(self):
        self.unbinded = True

    def remove_instance(self, instance):
        self.removed = True

    def is_ok(self):
        return self.ok, self.msg


class SharedManager(object):
    def __init__(self):
        self.server = get_value("REDIS_SERVER_HOST")

    def add_instance(self, instance_name):
        host = os.environ.get("REDIS_PUBLIC_HOST", self.server)
        port = os.environ.get("REDIS_SERVER_PORT", "6379")
        return Instance(
            name=instance_name,
            plan='development',
            endpoints=[{"host": host, "port": port}],
        )

    def bind(self, instance):
        endpoint = instance.endpoints[0]
        return {
            "REDIS_HOST": endpoint["host"],
            "REDIS_PORT": endpoint["port"],
        }

    def unbind(self):
        pass

    def remove_instance(self, instance):
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
    'shared': SharedManager,
    'fake': FakeManager,
    'docker': DockerManager,
}
