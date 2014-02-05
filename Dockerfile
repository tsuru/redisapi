FROM        ubuntu
EXPOSE      6379 26379
ADD         redis-sentinel.sh /usr/bin/
RUN         apt-get update && apt-get install -y software-properties-common python-software-properties
RUN         /usr/bin/add-apt-repository ppa:chris-lea/redis-server
RUN         apt-get update
RUN         apt-get -y --force-yes install redis-server
RUN         touch /tmp/sentinel.conf
CMD         ["--loglevel warning --maxmemory 1073741824"]
ENTRYPOINT  ["/usr/bin/redis-sentinel.sh"]
