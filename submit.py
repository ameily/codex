
from __future__ import print_function, division
import os
import sys

import mongoengine as db
from codex import formats
from codex.models import Sample
import pefile
import argparse
import threading
import time


MAX_FILE_SIZE = 268435456 # 256 Mb


class Status:

    def __init__(self):
        self.dups = self.count = self.invalids = self.bytes = 0
        self.running = True

status = Status()


def humanize_bytes(bytes, precision=1):
    """Return a humanized string representation of a number of bytes.

    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 byte'
    >>> humanize_bytes(1024)
    '1.0 kB'
    >>> humanize_bytes(1024*123)
    '123.0 kB'
    >>> humanize_bytes(1024*12342)
    '12.1 MB'
    >>> humanize_bytes(1024*12342,2)
    '12.05 MB'
    >>> humanize_bytes(1024*1234,2)
    '1.21 MB'
    >>> humanize_bytes(1024*1234*1111,2)
    '1.31 GB'
    >>> humanize_bytes(1024*1234*1111,1)
    '1.3 GB'
    """
    if bytes == 0:
        return '0 bytes'
    elif bytes == 1:
        return '1 byte'

    abbrevs = (
        (1<<50L, 'PB'),
        (1<<40L, 'TB'),
        (1<<30L, 'GB'),
        (1<<20L, 'MB'),
        (1<<10L, 'kB'),
        (1, 'bytes')
    )
    
    for factor, suffix in abbrevs:
        if bytes >= factor:
            break
    return '%.*f %s' % (precision, bytes / factor, suffix)


def parse_args():
    parser = argparse.ArgumentParser(description='import samples into codex')
    parser.add_argument('path', metavar='PATH', help='path to recursively import')
    return parser.parse_args()


def print_status():
    print(
        # Clear the line
        "\r\x1b[K",
        # Success
        "\x1b[1;32m", "{:>15,}".format(status.count), "\x1b[0m", " | ",
        # Dups
        "\x1b[1;36m", "{:>15,}".format(status.dups), "\x1b[0m",  " | "
        # Errors
        "\x1b[1;31m", "{:>15,}".format(status.invalids), "\x1b[0m", " | ",
        "\x1b[1;35m", "{:>15}".format(humanize_bytes(status.bytes)), "\x1b[0m",
        sep='', end=''
    )
    sys.stdout.flush()



def status_thread():
    print(
        "\x1b[1;32m", "{:>15}".format('Success'), "\x1b[0m", ' | ',
        "\x1b[1;36m", "{:>15}".format('Duplicates'), "\x1b[0m", ' | ',
        "\x1b[1;31m", "{:>15}".format("Failures"), "\x1b[0m", ' | ', 
        "\x1b[1;35m", "{:>15}".format("Bytes Saved"), "\x1b[0m\n",
        "=====================================================================",
        sep=''
    )
    while status.running:
        print_status()
        time.sleep(2)


def find_samples(root):
    for (dirpath, dirnames, filenames) in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)

            if os.path.getsize(path) > MAX_FILE_SIZE:
                continue

            fp = open(path, 'rb')
            data = fp.read()
            fp.close()

            (found, sample) = Sample.get_or_create(data)
            if found:
                status.dups += 1
            else:
                sample.original_name = name
                sample.namespace = formats.parse_namespace(dirpath[len(root):])
                if formats.populate_sample(sample, data):
                    status.count += 1
                    status.bytes += len(data)
                    sample.set_blob(data)
                    sample.save()
                else:
                    status.invalids += 1



if __name__ == '__main__':
    db.connect("codex")
    args = parse_args()

    # make sure path ends with a /
    root = os.path.join(os.path.abspath(args.path), '')
    t = threading.Thread(target=status_thread)
    t.start()

    try:
        find_samples(root)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.stdout.flush()
    except:
        import traceback
        traceback.print_exc()

    status.running = False
    t.join(10)
    print_status()
    print()

    
