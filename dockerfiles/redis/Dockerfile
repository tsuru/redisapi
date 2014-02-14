FROM        ubuntu
EXPOSE      6379
RUN         apt-get update && apt-get install -y software-properties-common python-software-properties
RUN         /usr/bin/add-apt-repository ppa:chris-lea/redis-server
RUN         apt-get update
RUN         apt-get -y --force-yes install redis-server
CMD         ["--loglevel warning --maxmemory 1073741824"]
ENTRYPOINT  ["/usr/bin/redis-server"]
