import argparse
import multiprocessing
import os
import re
import sys
import time

from typing import Tuple

import h5py
import progressbar

# Support for Perturbo eph_g2 pool files
from .poolfiles import *


DEFAULT_FROMDIR = './tmp'
FILE_REGEX = re.compile(r'([^_]+)_eph_g2_p(\d+)\.h5')

DEFAULT_MAX_PROCESSES = 50
SUBPROCESS_REPORT_INTERVAL = 3.0 # in seconds


def init_parser(subparsers):
    parser = subparsers.add_parser('reshape',
        help='Reshape Perturbo tmp/ files for a different number of pools.')

    parser.add_argument('-f', '--fromdir', default=DEFAULT_FROMDIR,
        help=f'Source directory to read eph_g2_p*.h5 files from.  Default is {DEFAULT_FROMDIR}.')

    parser.add_argument('-t', '--todir', required=True,
        help='Target directory to write reshaped eph_g2_p*.h5 files to.')

    parser.add_argument('-p', '--pools', type=int, required=True,
        help='Number of pools to generate in the target directory.')

    parser.add_argument('-n', '--dryrun', action='store_true',
        help='Perform a dry-run; don\'t write any target files out.')

    parser.add_argument('-q', '--quiet', action='store_true',
        help='Run in "quiet mode," with a minimum of output.')

    parser.add_argument('--mp', action='store_true',
        help='Use multiprocessing to speed up reshape operations.')

    parser.add_argument('-M', '--max-processes', type=int, default=DEFAULT_MAX_PROCESSES,
        help=f'Specify maximum number of subprocesses to use.  Default is {DEFAULT_MAX_PROCESSES}.')


def check_args(args):
    # Check arguments

    print(f'Reading pool files from {args.fromdir}')
    if not os.path.isdir(args.fromdir):
        print(f'ERROR:  {args.fromdir} is not a directory')
        sys.exit(1)

    if args.pools < 1:
        print(f'ERROR:  Number of pools must be positive; got {args.pools}')
        sys.exit(1)

    print(f'Writing {args.pools} pool files to {args.todir}')
    if os.path.exists(args.todir):
        existing_files = os.listdir(args.todir)
        if len(existing_files) > 0:
            print(f'ERROR:  Existing files found in {args.todir}, aborting.')
            sys.exit(1)

    if args.mp:
        print(f'\nUsing multiprocessing to speed up performance.  Max processes = {args.max_processes}.')

def file_scan_progress(pool, f, max_filename_len):
    # This is grungy because we want to add extra string padding after the
    # ':' character, not before it.
    out_filename = f.filename + ':  '
    if len(out_filename) < max_filename_len + 3:
        out_filename = out_filename + ' ' * (max_filename_len + 3 - len(out_filename))

    print(f' * {out_filename}nk_loc = {f.nk_loc}\tnkq = {f.nkq}')

def scan_source_directory(args):
    print(f'\nScanning source directory {args.fromdir}')

    sfset = PoolFileSet(args.fromdir)
    sfset.find_files()
    if sfset.num_pools == 0:
        print('ERROR:  Found no pool data files in source directory, aborting.')
        sys.exit(1)

    max_filename_len = max([len(f.filename) for f in sfset.pool_files.values()])

    if not args.quiet:
        print(f'Found {sfset.num_pools} files:')

    progress = None
    if not args.quiet:
        progress=lambda pool, f : file_scan_progress(pool, f, max_filename_len)

    if args.mp:
        sfset.scan_files_mp(progress=progress, max_processes=args.max_processes)
    else:
        sfset.scan_files(progress=progress)

    if not args.quiet:
        print(f'Total k-grid points:  {sfset.nkpt}\tTotal k-q pairs:  {sfset.nkq}')

    return sfset


def write_new_target_files(args, sfset):
    print(f'\nWriting new set of pool files to directory {args.todir}')

    if not os.path.exists(args.todir):
        print(f'NOTE:  {args.todir} doesn\'t exist; creating')
        os.makedirs(args.todir)

    tfset = PoolFileSet(args.todir)
    tfset.make_new_pool_files(sfset.prefix, args.pools)

    bar = progressbar.ProgressBar(max_value=sfset.nkpt)
    bar.start()
    for i_kloc in range(sfset.nkpt):
        (src_pool, src_idx) = kloc_index_to_pool_index(i_kloc, sfset.num_pools)
        (tgt_pool, tgt_idx) = kloc_index_to_pool_index(i_kloc, tfset.num_pools)

        src_f = sfset.pool_files[src_pool + 1]
        tgt_f = tfset.pool_files[tgt_pool + 1]

        tgt_f.set_eph_g2(tgt_idx + 1, src_f.get_eph_g2(src_idx + 1))
        tgt_f.set_bands_index(tgt_idx + 1, src_f.get_bands_index(src_idx + 1))

        bar.update(i_kloc + 1)
    bar.finish()
    tfset.close_all()
    return tfset


def mp_generate_perturbo_hdf5_file(filename, pool, num_pools, sfset, queue):
    sfset.open_all('r')

    tgt_f = PoolFile(filename, pool + 1)
    tgt_f.open('w')
    tgt_f.nk_loc = 0

    count = 0
    t = time.time()
    for i_kloc in range(pool, sfset.nkpt, num_pools):
        (src_pool, src_idx) = kloc_index_to_pool_index(i_kloc, sfset.num_pools)
        (tgt_pool, tgt_idx) = kloc_index_to_pool_index(i_kloc, num_pools)

        # All of the k-grid indexes we are traversing should map to this
        # specific target file.
        assert tgt_pool == pool, f'k-grid index {i_kloc} maps to {tgt_pool}, not expected pool {pool}'

        src_f = sfset.pool_files[src_pool + 1]

        tgt_f.set_eph_g2(tgt_idx + 1, src_f.get_eph_g2(src_idx + 1))
        tgt_f.set_bands_index(tgt_idx + 1, src_f.get_bands_index(src_idx + 1))

        tgt_f.nk_loc += 1

        count += 1
        t2 = time.time()
        if (t2 - t) >= SUBPROCESS_REPORT_INTERVAL:
            queue.put( (pool, count) )
            count = 0
            t = t2

    queue.put( (pool, count) )
    queue.put( (pool, None) )
    queue.close()


def mp_write_new_target_files(args, sfset, **kwargs):
    print(f'\nWriting new set of pool files to directory {args.todir}')

    if not os.path.exists(args.todir):
        print(f'NOTE:  {args.todir} doesn\'t exist; creating')
        os.makedirs(args.todir)

    max_processes = kwargs.get('max_processes', DEFAULT_MAX_PROCESSES)

    # Since we pass the source fileset to the subprocesses, we need to close
    # the HDF5 files since we can't pickle them.
    sfset.close_all()

    exec_pool = multiprocessing.Pool(max_processes)
    tasks = {}
    manager = multiprocessing.Manager()
    queue = manager.Queue()

    # Queue up a task for each target file we are writing.
    for tgt_pool in range(args.pools):
        tgt_filename = make_pool_filename(sfset.prefix, tgt_pool + 1)
        tgt_filename = os.path.join(args.todir, tgt_filename)

        r = exec_pool.apply_async(mp_generate_perturbo_hdf5_file,
            (tgt_filename, tgt_pool, args.pools, sfset, queue))

        tasks[tgt_pool] = r

    exec_pool.close()

    # Monitor the subprocesses for their completion.

    if not args.quiet:
        bar = progressbar.ProgressBar(max_value=sfset.nkpt)
        bar.start()

    count = 0
    while len(tasks) > 0:
        (tgt_pool, value) = queue.get()

        if value is None:
            # Finished processing specified pool.
            # TODO:  Not sure if this is necessary.  tasks[tgt_pool].get()
            del tasks[tgt_pool]
        else:
            count += value

            if not args.quiet:
                bar.update(count)

    if not args.quiet:
        bar.finish()

    # Clean up the executor pool.
    exec_pool.join()


def main(args):
    check_args(args)

    sfset = scan_source_directory(args)

    if not args.dryrun:
        if args.mp:
            mp_write_new_target_files(args, sfset, max_processes=args.max_processes)
        else:
            write_new_target_files(args, sfset)
    else:
        print('\nDry-run requested, not writing output files.')

    sfset.close_all()

    print('\nDone!')
    sys.exit(0)


if __name__ == '__main__':
    main()
