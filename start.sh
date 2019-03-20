#!/bin/sh

superconf -p $CPU_CORES
supervisord --nodaemon --configuration /etc/galloper.conf