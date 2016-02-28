import time

def print_time(func):
    def timed_func(*args, **kwargs):
        start_time = time.time()
        try:
            func()
        finally:
            end_time = time.time()
            print('Time: {:g} s'.format(end_time - start_time))
    return timed_func
