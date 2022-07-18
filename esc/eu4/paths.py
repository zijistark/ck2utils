import json
import warnings
import inspect
from localpaths import eu4dir, outpath, cachedir

_eu4_version = None


def eu4_version():
    global _eu4_version
    if _eu4_version is None:
        json_object = json.load(open(eu4dir / 'launcher-settings.json'))
        _eu4_version = json_object['rawVersion']

    return _eu4_version


def verified_for_version(version, extra_message=''):
    """issue a warning if the eu4 version is newer than the version parameter"""
    if version < eu4_version():
        warnings.warn(' The code in the function "{}" was last verified for eu4 version {}. '
                      'Please verify that it is still correct and update the version number. {}'.format(
                        inspect.stack()[1].function, version, extra_message), stacklevel=2)


eu4outpath = outpath / eu4_version()
if not eu4outpath.exists():
    eu4outpath.mkdir(parents=True)

if cachedir:
    eu4cachedir = cachedir / eu4_version()
else:
    eu4cachedir = None
