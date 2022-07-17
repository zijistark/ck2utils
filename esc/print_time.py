#!/usr/bin/env python3

import sys
import time

def print_time(func):
    def timed_func(*args, **kwargs):
        start_time = time.time()
        try:
            func(*args, **kwargs)
        finally:
            end_time = time.time()
            print('Time: {:g} s'.format(end_time - start_time),
                  file=sys.stderr)
    return timed_func
