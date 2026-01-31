#!/usr/bin/env python3
import csv, hashlib, os, sys

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MANIFEST=os.path.join(ROOT,'manifests','manifest_v6_2.csv')

def hfile(path, algo, chunk=1<<20):
    h=algo()
    with open(path,'rb') as fh:
        while True:
            b=fh.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def main():
    bad=0
    with open(MANIFEST, newline='', encoding='utf-8') as fh:
        rd=csv.DictReader(fh)
        for row in rd:
            rel=row['relative_path']
            full=os.path.join(ROOT, rel)
            if not os.path.exists(full):
                print('MISSING', rel)
                bad+=1
                continue
            md5=hfile(full, hashlib.md5)
            sha=hfile(full, hashlib.sha256)
            if md5!=row['md5'] or sha!=row['sha256']:
                print('HASH_MISMATCH', rel)
                print('  expected md5  ', row['md5'])
                print('  actual   md5  ', md5)
                print('  expected sha256', row['sha256'])
                print('  actual   sha256', sha)
                bad+=1
    if bad:
        print('FAILED', bad)
        return 1
    print('OK')
    return 0

if __name__=='__main__':
    sys.exit(main())
