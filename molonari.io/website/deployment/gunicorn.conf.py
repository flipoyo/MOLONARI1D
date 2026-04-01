# Gunicorn configuration for molonari.io
# Usage: gunicorn -c deployment/gunicorn.conf.py molonari_site.wsgi

import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
accesslog = "-"
errorlog = "-"
