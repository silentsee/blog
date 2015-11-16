import config_default


def merge(default, override):
    r = {}
    for k, v in default.iteritems():#default is a dict and by default you are iterating over just the keys (which are strings).Since default has more than two keys*, they can't be unpacked into the tuple "k, m", hence the ValueError exception is raised.
        if k in override:
            if isinstance(v,dict):
                r[k] = merge(v,override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

configs = config_default.configs

try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass


