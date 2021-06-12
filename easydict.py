#!/usr/bin/python

import collections

# auto-vivify nested dicts of any depth
class autodict(collections.defaultdict):
    def __init__(self, *other, **kw):
        collections.defaultdict.__init__(self, type(self), *other, **kw)

    def __add__(self, other):
        return other

    __repr__ = dict.__repr__


# recursively convert/upgrade a dict to some kind of fancy dict
def dconvert(dtype, d):
    if isinstance(d, dict):
        return   dtype( dconvert(dtype, x) for x in d.items() )
    if isinstance(d, (tuple, list)):
        return type(d)( dconvert(dtype, x) for x in d )
    return d


# wrap a class with dconvert, and allow dict-like init with kwargs
def dconverter__init(dtype):
    def converter(_d=None, **_kw):
        d = _kw if _d is None else dict(_d, **_kw) if _kw else _d
        return dconvert(dtype, d)
    return converter


# read-write attribute access to dict keys, with auto-vivification
@dconverter__init
class easydict_av(autodict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, val):
        self[name] = val


# read-write attribute access to dict keys, no auto-vivification
@dconverter__init
class easydict(dict):
    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, name, val):
        self[name] = val


