import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from localpaths import eu4dir,  outpath

def eu4_version():
    json_object = json.load(open(eu4dir / 'launcher-settings.json'))
    return json_object['rawVersion']

def eu4_major_version():
    return '.'.join(eu4_version().split('.')[0:2])

eu4outpath = outpath / eu4_version()
if not eu4outpath.exists():
    eu4outpath.mkdir(parents=True)

