#!/bin/bash

galloper_uwsgiconf
superconf -p $CPU_CORES
supervisord --configuration /etc/galloper.conf
sleep 5
tail -f /var/log/worker.log