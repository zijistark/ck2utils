#!/usr/bin/env python3

import math
import random
import numpy as np
from print_time import print_time

def mtth(x):
    return random.expovariate(math.log(2) / x)

def trial1():
    league = 1550 + mtth(10)
    if league > 1575:
        league = 1575 + mtth(5)
        if league > 1600:
            league = 1600 + mtth(0.5)
    diet = league + 30 + mtth(5)
    return diet

def trial2():
    diet = 1625 + mtth(5)
    return diet

@print_time
def main():
    trials = 100000
    for i, func in enumerate([trial1, trial2]):
        a = np.fromiter(iter(func, None), np.float, trials)
        q = np.percentile(a, [25, 50, 75], overwrite_input=True)
        print('{0}: {2:.2f} ({1:.2f}-{3:.2f} @ 50%)'.format(i + 1, *q))

if __name__ == '__main__':
    main()
