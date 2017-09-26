#!/usr/bin/env python3

import argparse
from pathlib import Path
import pickle
import re
from ck2parser import rootpath, vanilladir, cachedir, is_codename, SimpleParser
from print_time import print_time


parser = SimpleParser()

digestible_mods = ['SWMH']

digest_dir = cachedir / 'digests'


def parse_arguments():
    argparser = argparse.ArgumentParser(
        description='Create and compare mod digests for save-compatibility.')
    argparser.add_argument('mod', nargs='+', type=Path, help='mod path')

    args = argparser.parse_args()

    for path in args.mod:
        if not path.is_dir():
            raise ValueError('{} is not an existing directory'.format(path))
        if not path.name in digestible_mods:
            raise ValueError("don't know how to digest {}".format(path.name))

    return args


def compatible_digests(old_digest, new_digest):
    compatible = True
    for k, v in old_digest.items():
        compatible &= v <= new_digest[k]
    return compatible


def create_digest_SWMH(mod_path):
    digest = {}
    titles = set()
    for _, tree in parser.parse_files('common/landed_titles/*'):
        dfs = list(tree)
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                titles.add(n.val)
                dfs.extend(v)
    digest['landed_titles'] = titles
    return digest


def record_digest(mod_path):
    parser.moddirs = [mod_path]
    if mod_path.name == 'SWMH':
        digest = create_digest_SWMH(mod_path)
    else:
        raise ValueError("don't know how to digest {}".format(mod_path.name))

    out_path = digest_dir / mod_path.name / 'latest'

    if out_path.exists():
        with out_path.open('rb') as f:
            old_digest = pickle.load(f, fix_imports=False)

        compatible = compatible_digests(old_digest, digest)

        if compatible:
            print('compatible')
        else:
            print('incompatible')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('wb') as f:
        pickle.dump(digest, f, protocol=-1, fix_imports=False)


def invalidate_repo_cache(bad_path=None):
    parser.invalidate_repo_cache(bad_path)


@print_time
def main():
    args = parse_arguments()
    for mod_path in args.mod:
        record_digest(mod_path)

    # no_title = []
    # for path in parser.files('gfx/flags/*.tga'):
    #     try:
    #         titles.remove(path.stem)
    #     except ValueError:
    #         if vanilladir not in path.parents:
    #             no_title.append(path.name)
    # no_flag = [t for t in titles if not t.startswith('b')]
    # with (rootpath / 'flags.txt').open('w') as f:
    #     if no_title:
    #         print('No title for flag:', *no_title, sep='\n\t', file=f)
    #     if no_flag:
    #         print('No flag for title:', *no_flag, sep='\n\t', file=f)


if __name__ == '__main__':
    main()
