import argparse
import os
import sys

from .poolfiles import *


def init_parser(subparsers):
    parser = subparsers.add_parser('analyze',
        help='Analyze Perturbo tmp/ pool files and report statistics.')

    parser.add_argument('-f', '--fromdir', default=DEFAULT_FROMDIR,
        help=f'Source directory to read eph_g2_p*.h5 files from.  Default is {DEFAULT_FROMDIR}.')

    parser.add_argument('--mp', action='store_true',
        help='Use multiprocessing to speed up analyze operations.')

    parser.add_argument('-M', '--max-processes', type=int, default=DEFAULT_MAX_PROCESSES,
        help=f'Specify maximum number of subprocesses to use.  Default is {DEFAULT_MAX_PROCESSES}.')


def check_args(args):
    # Check arguments

    print(f'Reading pool files from {args.fromdir}')
    if not os.path.isdir(args.fromdir):
        print(f'ERROR:  {args.fromdir} is not a directory')
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

    print(f'Found {sfset.num_pools} files:')

    progress=lambda pool, f : file_scan_progress(pool, f, max_filename_len)
    if args.mp:
        sfset.scan_files_mp(progress=progress, max_processes=args.max_processes)
    else:
        sfset.scan_files(progress=progress)

    return sfset


def main(args):
    check_args(args)

    sfset = scan_source_directory(args)
    print(f'\nTotal k-grid points:  {sfset.nkpt}\tTotal k-q pairs:  {sfset.nkq}')

    sfset.close_all()
    sys.exit(0)

if __name__ == '__main__':
    main()
