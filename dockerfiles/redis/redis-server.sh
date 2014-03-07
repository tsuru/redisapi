#!/bin/bash
/usr/bin/redis-server --loglevel warning --maxmemory 1073741824 --port $REDIS_PORT
