#!/bin/sh
gunicorn  run:app -w 2 --log-level 'debug' --threads 2 -b 0.0.0.0:80