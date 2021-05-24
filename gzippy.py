#!/usr/bin/python

import StringIO
import gzip

# pre-python3.2 equivalents of gzip.decompress / gzip.compress

def gunzip(data):
    sio = StringIO.StringIO(data)
    return gzip.GzipFile(fileobj=sio).read()


def gzip_bytes(data):
    sio = StringIO.StringIO()
    gzip.GzipFile(fileobj=sio, mode="wb").write(data)
    return sio.getvalue()


decompress = gunzip
compress   = gzip_bytes

