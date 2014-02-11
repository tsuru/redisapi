# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import json
import redis
import docker

from hc import health_checkers
from utils import get_value
from storage import MongoStorage, Instance


class DockerHaManager(object):

    def health_checker(self):
        hc_name = os.environ.get("HEALTH_CHECKER", "fake")
        return health_checkers[hc_name]()


class DockerManager(object):
    def __init__(self):
        self.server = get_value("REDIS_SERVER_HOST")
        self.image_name = get_value("REDIS_IMAGE")
        docker_hosts = get_value("DOCKER_HOSTS")
        self.docker_hosts = json.loads(docker_hosts)

        self.storage = MongoStorage()

    def client(self):
        return docker.Client(base_url='unix://var/run/docker.sock')

    def health_checker(self):
        hc_name = os.environ.get("HEALTH_CHECKER", "fake")
        return health_checkers[hc_name]()

    def add_instance(self, instance_name):
        output = self.client().create_container(self.image_name, command="")
        self.client().start(output["Id"], port_bindings={6379: ('0.0.0.0',)})
        container = self.client().inspect_container(output["Id"])
        port = container['NetworkSettings']['Ports']['6379/tcp'][0]['HostPort']
        instance = Instance(
            name=instance_name,
            container_id=output["Id"],
            host=self.server,
            port=port,
            plan='basic',
        )
        self.health_checker().add(self.server, port)
        return instance

    def bind(self, instance):
        return {
            "REDIS_HOST": instance.host,
            "REDIS_PORT": instance.port,
        }

    def unbind(self):
        pass

    def remove_instance(self, instance):
        self.client().stop(instance.container_id)
        self.client().remove_container(instance.container_id)
        self.health_checker().remove(self.server, instance.port)

    def is_ok(self):
        pass


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
            host=host,
            port=port,
            plan='development',
            container_id='',
        )

    def bind(self, instance):
        return {
            "REDIS_HOST": instance.host,
            "REDIS_PORT": instance.port,
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
