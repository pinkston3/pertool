import argparse
import sys

from . import generate
from . import reshape


def make_parser():
    parser = argparse.ArgumentParser(prog='pertool')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # "reshape" command
    reshape.init_parser(subparsers)

    # "generate" command
    generate.init_parser(subparsers)

    # TODO:  "multigen" command

    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()

    if args.command == 'reshape':
        reshape.main(args)
    elif args.command == 'generate':
        generate.main(args)
    else:
        print(f'ERROR:  Unrecognized command:  {args.command}')
        sys.exit(1)

    sys.exit(0)