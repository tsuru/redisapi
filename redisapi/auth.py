# Copyright 2015 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import requests

import os


class Unauthorized(Exception):
    pass


def scheme_info():
    tsuru_host = os.environ.get("TSURU_HOST")
    url = '{0}/auth/scheme'.format(tsuru_host)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}


def user_info(token):
    url = ""
    response = requests.get(url)
    if response.status_code > 399:
        raise Unauthorized()
