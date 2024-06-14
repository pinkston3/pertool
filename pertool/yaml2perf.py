import os
import sys

import yaml


PERF_DATA = [
    ('grid', 'number of  tetrahedra selected'),
    ('grid', 'number of reducible k-points'),
    ('grid', 'number of irreducible k-points'),
    ('scatter parallelization', 'total number of q-points'),
    ('scatter parallelization', 'total number of (k,q) pairs'),
    ('memory', 'physical'),
    ('memory', 'max rss'),
    ('memory', 'gpu in-use'),
    ('kq_pair [intermediate]', 'bytes per entry'),
    ('kq_pair [intermediate]', 'total bytes allocated'),
    ('scat', 'bytes per entry'),
    ('scat', 'total bytes allocated'),
    ('scatter', 'bytes per entry'),
    ('scatter', 'total bytes allocated'),
    ('scatter_channels', 'bytes per entry'),
    ('scatter_channels', 'total bytes allocated'),
    ('scatter_paths [intermediate]', 'bytes per entry'),
    ('scatter_paths [intermediate]', 'total bytes allocated'),
    ('scatter_targets', 'bytes per entry'),
    ('scatter_targets', 'total bytes allocated'),
    ('scattgts_sources', 'bytes per entry'),
    ('scattgts_sources', 'total bytes allocated'),
    ('timings', 'scat_setup', 'wall'),
    ('timings', 'target_setup', 'wall'),
    ('timings', 'dynamics_tot', 'wall'),
    ('timings', 'dynamics_col', 'wall'),
    ('timings', 'dynamics_col', 'calls'),
]


def get_value(data, *path, missing=''):
    part = data
    for step in path:
        part = part.get(step)
        if part is None:
            return missing

    return str(part)


def yaml2perf(filepath):
    with open(filepath) as f:
        data = yaml.load(f, Loader=yaml.Loader)

    values = []
    values.append(os.path.basename(filepath))
    for key in PERF_DATA:
        values.append(get_value(data, *key))

    return values


if __name__ == '__main__':
    header = ['filepath']
    for key in PERF_DATA:
        header.append('.'.join(key))

    rows = []
    for filepath in sys.argv[1:]:
        rows.append(yaml2perf(filepath))

    print('\t'.join(header))
    for row in rows:
        print('\t'.join(row))
