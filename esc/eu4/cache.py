import pickle
import numpy
from functools import wraps
from eu4.paths import eu4cachedir

try:
    from functools import cached_property
except: # for backwards compatibility with python versions < 3.8
    from functools import lru_cache
    def cached_property(f):
        return property(lru_cache()(f))


class PickleSerializer:

    @staticmethod
    def get_file_extension():
        return 'pkl'

    @staticmethod
    def serialize(data, filename):
        pickle.dump(data, open(filename, 'wb'))

    @staticmethod
    def deserialize(filename):
        return pickle.load(open(filename, 'rb'))


class NumpySerializer:

    @staticmethod
    def get_file_extension():
        return 'npy'

    @staticmethod
    def serialize(data, filename):
        numpy.save(filename, data)

    @staticmethod
    def deserialize(filename):
        return numpy.load(filename)


def disk_cache(serializer=PickleSerializer):
    """Cache the method result on disk

    Warning: the cache assumes that the return value does not change
    as long as the eu4 version stays the same. When changing the code
    of the decorated method, you have to clear the cache manually

    setting eu4cachedir to None disables the cache, but it doesn't clear it
    """
    def decorating_function(f):
        if not eu4cachedir:
            return f

        @wraps(f)
        def wrapper(self):
            cachedir_with_module = eu4cachedir / f.__module__
            cachedir_with_module.mkdir(parents=True, exist_ok=True)
            cachefile = cachedir_with_module / (f.__name__ + '.' + serializer.get_file_extension())
            if cachefile.exists():
                return serializer.deserialize(cachefile)
            else:
                return_value = f(self)
                serializer.serialize(return_value, cachefile)
                return return_value
        return wrapper
    return decorating_function
