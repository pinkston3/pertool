import argparse
import sys

from . import analyze
from . import generate
from . import reshape


COMMANDS = {
    'analyze': analyze,
    'generate': generate,
    'reshape': reshape,
}


def make_parser():
    parser = argparse.ArgumentParser(prog='pertool')
    subparsers = parser.add_subparsers(dest='command', required=True)

    for module in COMMANDS.values():
        module.init_parser(subparsers)

    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()

    if args.command in COMMANDS:
        COMMANDS[args.command].main(args)

    else:
        print(f'ERROR:  Unrecognized command:  {args.command}')
        sys.exit(1)

    sys.exit(0)