#!/usr/bin/python

import collections

class autodict(collections.defaultdict):
    def __init__(self, *other, **kw):
        collections.defaultdict.__init__(self, type(self), *other, **kw)

    def __add__(self, other):
        return other

    __repr__ = dict.__repr__


# read-write attribute access to dict keys
class _easydict(autodict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, val):
        self[name] = val


# recursively convert/upgrade a dict to some kind of fancy dict

def dconvert(dtype, d):
    if isinstance(d, dict):
        return   dtype( dconvert(dtype, x) for x in d.items() )
    if isinstance(d, (tuple, list)):
        return type(d)( dconvert(dtype, x) for x in d )
    return d


def easydict(d):
    return dconvert(_easydict, d)

