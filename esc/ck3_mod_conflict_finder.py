from collections import defaultdict
from pathlib import Path
import sqlite3
from ck3parser import rootpath
from print_time import print_time

checksummed = {'common', 'events', 'history',
               'map_data', 'gui', 'localization', 'data_binding'}

conflict_free = {Path(p) for p in [
    'CHANGELOG.md',
    'descriptor.mod',
    'LICENSE.md',
    'notes.txt',
    'README.md',
    'thumbnail_long.png',
    'thumbnail.png',
    'thumbnailwide.png',
]}

#atm:
# light works, heavy crashes, apparently because of ibl, though both do have script errors
# adding bap fixes ibl.
# removing all non-cmh doesn't fix ibl.
# 100% cmh works.
# 100% cmh minus bap? crashes. w/o cccmh? crashes.
# 100% cmh minus ibl and bap? works.
# ibl by itself? works.
# so something in cmh makes ibl require bap.
# ibl,epe,ibtp,cccmh? crashes.
# ibl,ibtp,cccmh? crashes.
# ibl,cccmh? works.
# ibl,ibtp? crashes.

# more holding graphics (~cmh) and ibn battuta's legacy (cmh) seem incompatible
# heavy gets ibl, light gets mhg
# (mhg & mhg+cfp compatch go together)

# rice might be incompatible with ibl and bap without cccmh compatch, which might require bap, sinews of war, loyal to a fault, but i think it doesn't so i'm enabling it

# morven's mods added only for kg's compatch:
# Hostile Struggles, Doctor Tweak, Hagia Sophia, Pacification, Total Animation, Artifact Claims Nerf, Title-Ranked Portrait Borders

# unofficial patch goes first
# before uniui: inherichance
# in my humble opinion -> gamerule gadget -> foundational framework
# more holding graphics says: mhg+cfp -> mhg -> community flavor pack

# [not applied] At the top: Character beautification
#   > Traits
#   > Barbershop related beatification
#   > Game mechanics related to traits
#   > overall game graphics
#   > Holdings
#   > Descisions
#   > Interface
#   > Game mechanics
#   > Mechanics & Interface (culture and faith related)
#   > Total conversion Mods (bigger mods like BAP ME EPE CFP etc.)
#   > Compatches in the stated order by the authors.

# compatible_mods =
# 1. mod B is a submod for mod A
#    -> ignore all AB conflicts (keep ABx conflicts)
#    -> either load B after all other mods, or load A before all other mods (have to build dag and traverse)
# 2. mod C is a compatibility patch for mods A and B.
#    -> if ABC all in playset, ignore all AB, AC, BC, and ABC conflicts (keep ABx, ACx, BCx, ABCx conflicts)
#    should i decompose this into two instances of [1]?

# maybe instead just "these 4 mods play nice together" without bothing about whether all 4 are needed or if any subset is also fine? but then we can't generate load order nicely.

# current mod order: lexicographic on file list (heuristic for 'mod category')
#    can read tags from db, sort on tags instead. maybe better.
# mod order should be: overhauls first, then "non-framework-related", then frameworks, then framework-related?
# or... cosmetic, then mechanical?


mod_db_path = Path.home() / \
    'Documents/Paradox Interactive/Crusader Kings III/launcher-v2.sqlite'


@print_time
def main():
    affects_checksum = set()
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
                if file.parts[0] in checksummed:
                    affects_checksum.add(mod)
    for playset, playset_mods in playsets.items():
        playset_conflicts[playset] = defaultdict(list)
        for file, file_mods in mods_of_files.items():
            mods = frozenset(playset_mods & file_mods)
            if len(mods) > 1 and conflict_free.isdisjoint({file, *file.parents}):
                playset_conflicts[playset][mods].append(file)

    with open(rootpath / 'ck3_mod_conflicts.txt', 'w') as f:
        print('Checksum-invariant mods:', file=f)
        for mod in sorted(all_mods):
            if mod not in affects_checksum:
                print(f'\t{mod}', file=f)
        for playset, conflicts in sorted(playset_conflicts.items()):
            print(playset, file=f)
            for mod in sorted(playsets[playset], key=(lambda m: sorted(files_of_mod[m]))):
                print(f'\t{mod}', file=f)
            if not conflicts:
                print('\t<no conflicts>', file=f)
            for mods, files in sorted(conflicts.items()):
                print('\t' + '; '.join(sorted(mods)), file=f)
                for file in sorted(files):
                    print(f'\t\t{file.as_posix()}', file=f)


if __name__ == '__main__':
    main()
