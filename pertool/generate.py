import argparse
import json
import os
import sys

from typing import Any, Optional


DEFAULT_CONFIGFILE = 'mp_conf.json'


def generate_target_dir(source_path, target_path, config):
    if 'steps' not in config:
        raise ValueError('No steps specified in configuration, aborting.')


def init_parser(subparsers) -> None:
    parser = subparsers.add_parser('generate',
        help='Generate Perturbo config files and scripts to run one simulation.')

    parser.add_argument('-f', '--fromdir', required=True,
        help=f'Source directory to use as a template.')

    parser.add_argument('-t', '--todir', required=True,
        help='Target directory to write generated files to.')

    parser.add_argument('-c', '--config',
        help='Config file to drive the generation operation.  If '
             'unspecified, the "mp_conf.json" file in the source '
             'directory is used.')


def check_args(args):
    # Check arguments

    print(f'Reading files from template directory {args.fromdir}')
    if not os.path.isdir(args.fromdir):
        print(f'ERROR:  {args.fromdir} is not a directory')
        sys.exit(1)

    print(f'Writing generated results to output directory {args.todir}')
    if not os.path.exists(args.todir):
        print(f'NOTE:  {args.todir} doesn\'t exist; creating')
        os.makedirs(args.todir)
    else:
        existing_files = os.listdir(args.todir)
        if len(existing_files) > 0:
            print(f'ERROR:  Existing files found in {args.todir}, aborting.')
            sys.exit(1)


def main(args: Optional[argparse.Namespace]=None) -> None:
    if args is None:
        parser = argparse.ArgumentParser(description='Generate Perturbo '
            'config files and scripts to run one simulation.')
        init_parser(parser)
        args = parser.parse_args()

    check_args(args)

    config_path = args.config
    if config_path is None:
        config_path = os.path.join(args.fromdir, DEFAULT_CONFIGFILE)

    print(f'Loading config file "{config_path}"')
    with open(config_path) as f:
        config = json.load(f)

    generate_target_dir(args.fromdir, args.todir, config)

    print('\nDone!')
