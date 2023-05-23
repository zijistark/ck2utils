from collections import defaultdict
from pathlib import Path
import sqlite3
from ck3parser import rootpath
from print_time import print_time

conflict_free = {Path(p) for p in [
    'descriptor.mod',
    'thumbnail.png'
]}

mod_db_path = Path.home() / \
    'Documents/Paradox Interactive/Crusader Kings III/launcher-v2.sqlite'


@print_time
def main():
    all_mods = {}
    playsets = defaultdict(set)
    con = sqlite3.connect(mod_db_path)
    for mod, path in con.execute("SELECT displayName, dirPath FROM mods WHERE status = 'ready_to_play'"):
        assert mod not in all_mods
        all_mods[mod] = Path(path)
    for playset, mod in con.execute("SELECT p.name, m.displayName FROM playsets_mods AS pm JOIN playsets AS p ON pm.playsetId = p.id JOIN mods AS m ON pm.modId = m.id"):
        if mod in all_mods:
            playsets[playset].add(mod)
    con.close()
    mods_of_files = defaultdict(set)
    files_of_mod = defaultdict(list)
    playset_conflicts = {}
    for mod, mod_path in all_mods.items():
        for path in mod_path.rglob('*'):
            if path.is_file():
                file = path.relative_to(mod_path)
                mods_of_files[file].add(mod)
                files_of_mod[mod].append(file)
    for playset, playset_mods in playsets.items():
        playset_conflicts[playset] = defaultdict(list)
        for file, file_mods in mods_of_files.items():
            mods = frozenset(playset_mods & file_mods)
            if len(mods) > 1 and conflict_free.isdisjoint({file, *file.parents}):
                playset_conflicts[playset][mods].append(file)

    with open(rootpath / 'ck3_mod_conflicts.txt', 'w') as f:
        for playset, conflicts in sorted(playset_conflicts.items()):
            print(playset, file=f)
            for mod in sorted(playsets[playset], key=(lambda m: sorted(files_of_mod[m]))):
                print(f'\t{mod}', file=f)
            for mods, files in sorted(conflicts.items()):
                print('\t' + '; '.join(sorted(mods)), file=f)
                for file in sorted(files):
                    print(f'\t\t{file.as_posix()}', file=f)
            else:
                print('\t<no conflicts>', file=f)


if __name__ == '__main__':
    main()
