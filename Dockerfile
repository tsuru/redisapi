FROM        ubuntu
RUN         add-apt-repository ppa:tsuru/redis-server
RUN         apt-get update
RUN         apt-get -y --force-yes install redis-server
EXPOSE      6379
CMD         ["--loglevel warning"]
CMD         ["--maxmemory 1073741824"]
ENTRYPOINT  ["/usr/bin/redis-server"]
