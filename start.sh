#!/bin/bash

uwsgiconf
superconf
supervisord --configuration /etc/galloper.conf
sleep 5
tail -f /tmp/supervisord.log
