"""Reuse TLS connections without sharing mutable Sessions between threads."""
import threading
import requests

_local = threading.local()

def http_session():
    if not hasattr(_local, 'session'):
        _local.session = requests.Session()
    return _local.session
