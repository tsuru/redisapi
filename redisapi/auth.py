# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import requests

import os


def scheme_info():
    tsuru_host = os.environ.get("TSURU_HOST")
    url = '{0}/auth/scheme'.format(tsuru_host)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}
