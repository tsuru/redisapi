#!/bin/bash
/usr/bin/redis-server $@ &
/usr/bin/redis-server /tmp/sentinel.conf --sentinel --port 26379 --loglevel warning
