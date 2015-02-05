
import os
from codex.formats import win32


def parse_namespace(path):
    parts = filter(lambda x: len(x) > 0, path.split(os.path.sep))
    return '/'.join(parts)

def populate_sample(*args, **kwargs):
    return win32.populate_sample(*args, **kwargs)
