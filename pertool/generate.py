import argparse
import json
import os
import shutil
import sys

from typing import Any, Optional

import jinja2
import pathvalidate
import yaml


DEFAULT_CONFIGFILE_JSON = 'mp_conf.json'
DEFAULT_CONFIGFILE_YAML = 'mp_conf.yml'

LARGE_FILE_THRESHOLD = 1_000_000_000


def init_parser(subparsers) -> None:
    parser = subparsers.add_parser('generate',
        help='Generate Perturbo config files and scripts to run one simulation.')

    parser.add_argument('-f', '--fromdir', required=True,
        help=f'Source directory to use as a template.')

    parser.add_argument('-t', '--todir', required=True,
        help='Target directory to write generated files to.  This path may ' +
             'include template parameters using Python\'s formatted-string ' +
             'syntax.  For example, the path "si-{gridsize}-{progname}" ' +
             'would result in paths with the variables "gridsize" and ' +
             '"progname" substituted into the path.  This can be useful ' +
             'with the --foreach argument to generate multiple ' +
             'configurations from a single template.\n\n' +
             'If a target path already exists then the program terminates ' +
             'at that point.  It will not overwrite existing files.')

    parser.add_argument('-c', '--config',
        help='Config file to drive the generation operation.  If '
             'unspecified, the "mp_conf.json" file in the source '
             'directory will be used.')

    parser.add_argument('-n', '--dryrun', action='store_true',
        help='Perform a dry-run; don\'t write any target files out.')

    parser.add_argument('-v', '--verbose', action='store_true',
        help='Turn on verbose output.')

    parser.add_argument('-s', '--set', action='append', default=[],
        metavar='NAME=VALUE',
        help='Specify a variable name and value in "name=value" form.  ' +
             'The double-quotes may or may not be required around the ' +
             'variable specification, if name or value includes spaces or ' +
             'other characters that are meaningful to the command-shell.')

    parser.add_argument('--foreach', action='append', default=[],
        metavar='NAME=[VAL1,VAL2,...]',
        help='Specify a variable name and series of values in ' +
             '"name=[v1,v2,...]" form.  Template generation is run once ' +
             'for each value specified for the variable.  If multiple ' +
             '--foreach arguments are specified then the program will ' +
             'run template generation for all combinations of all ' +
             'variables specified.\n\n' +
             'Using a parameterized value for --todir is recommended when ' +
             'using this feature.')

"""



def generate_target_dir(template_dir, target_dirname_template, template_context,
        symlink_large_files=False) -> str:
    '''
    Generate a target directory from a template source directory, and also
    a set of variables and their values.
    '''
    if not os.path.isdir(template_dir):
        raise ValueError(f'template_directory {template_dir} isn\'t a directory')

    target_dirname = get_target_dirname(target_dirname_template, template_context)
    if os.path.exists(target_dirname):
        raise ValueError('Generated target directory name already exists')

    files = os.listdir(template_dir)
    templates = []
    to_copy = []
    for f in files:
        if f.endswith('.tmpl'):
            templates.append(f)
        else:
            to_copy.append(f)

    os.makedirs(target_dirname)

    # TODO:  handle templates
    for f in templates:
        generate_template_to_dir(f, target_dirname, template_context)

    # Copy over all non-template files
    for f in to_copy:
        copy_file_to_dir(f, target_dirname, symlink_large_files=symlink_large_files)
"""

def foreach_generate_target_dir_contents(foreach_vars, args, config, input_vars=None):
    if input_vars is None:
        input_vars = {}

    if not foreach_vars:
        generate_target_dir_contents(args, config, input_vars)
        return

    # This invocation takes care of the "foreach"-variable at the
    # start of the list.  Pull it off, then recursively call
    # foreach_generate_target_dir() to handle the next one.
    (name, lst) = foreach_vars[0]
    tail_foreach_vars = foreach_vars[1:]
    for value in lst:
        vars = dict(input_vars)
        vars[name] = value
        foreach_generate_target_dir_contents(tail_foreach_vars, args, config, vars)


def generate_target_dir_contents(args, config, input_vars=None):
    # Set up the variables for this target directory

    if input_vars is None:
        input_vars = {}

    global_vars = dict(input_vars)
    global_vars.update(config.get('variables', {}))

    # Make the target directory to generate stuff into

    todir = make_target_dir(args, global_vars)

    # Go through all specified generation steps, generating output files
    # for all specified template files.

    template_files = set()

    steps = config.get('steps', [])
    if not steps:
        print('Configuration contains no steps!')
        return

    jinja_loader = jinja2.FileSystemLoader(args.fromdir)
    jinja_env = jinja2.Environment(loader=jinja_loader, undefined=jinja2.StrictUndefined)

    step_i = 0
    for step_config in steps:
        step_i += 1
        if 'name' not in step_config:
            raise RuntimeError(f'Step {step_i} has no "name" attribute')

        step_name = step_config['name']
        print(f'\nStep {step_i}:  {step_name}')

        vars = dict(global_vars)
        vars.update(step_config.get('variables', {}))

        if args.verbose:
            print('\nVariables:')
            for (k, v) in vars.items():
                print(f'  {k} = {v}')
            print()

        templates = step_config.get('templates', [])
        if not templates:
            print('No templates to process.')
        else:
            for tmpl in templates:
                input_template = tmpl['input']
                template_files.add(input_template)

                output_file = make_template_filename(tmpl['output'], vars)
                output_path = os.path.join(todir, output_file)

                print(f'Processing template "{input_template}" into "{output_path}"')
                generate_template_to_file(jinja_env, input_template, vars, output_path)

    # Finally, copy over all other non-template files from the source
    # directory into the target directory.

    source_files = os.listdir(args.fromdir)
    for filename in source_files:
        # TODO:  Would be good to exclude config file as well
        if filename in template_files:
            continue

        copy_file_to_dir(os.path.join(args.fromdir, filename), todir)


def make_target_dir(args, vars):
    todir = make_template_filename(args.todir, vars)
    print(f'Writing generated results to output directory "{todir}"')

    if not os.path.exists(todir):
        print(f'NOTE:  "{todir}" doesn\'t exist; creating')
        os.makedirs(todir)

    # else:
    #     existing_files = os.listdir(todir)
    #     if len(existing_files) > 0:
    #         print(f'ERROR:  Existing files found in "{todir}", aborting.')
    #         sys.exit(1)

    return todir


def make_template_filename(template_str: str, variables: dict) -> str:
    ''' Generate a target filename using a template string. '''
    result = template_str.format_map(variables)

    # Raise an exception if the generated filepath is invalid.
    pathvalidate.validate_filepath(result)

    return result


def generate_template_to_file(jinja_env, source_file, variables, output_path):
    template = jinja_env.get_template(source_file)
    output_text = template.render(**variables)

    with open(output_path, 'w') as f:
        f.write(output_text)


def copy_file_to_dir(source_filepath, target_dir, symlink_large_files=False):
    target_file = os.path.join(target_dir, os.path.basename(source_filepath))

    filesize = os.path.getsize(source_filepath)
    if symlink_large_files and filesize >= LARGE_FILE_THRESHOLD:
        print(f'Sym-linking large file "{source_filepath}" into output directory "{target_dir}"')
        os.symlink(source_filepath, target_file)
    else:
        print(f'Copying "{source_filepath}" into output directory "{target_dir}"')
        shutil.copyfile(source_filepath, target_file)


def parse_arg_setvar(s: str) -> tuple[str, str]:
    '''
    Parse a --set NAME=VALUE argument into a (name,value) tuple.
    The name and value have whitespace stripped off of them.
    '''
    (name,eq,value) = s.partition('=')
    if not eq:
        raise RuntimeError(f'Bad --set argument "{s}":  missing =')

    name = name.strip()
    value = value.strip()

    return (name, value)

def parse_arg_foreach(s: str) -> tuple[str, list]:
    '''
    Parse a --foreach NAME=[VAL1,VAL2,...] argument into a (name,list) tuple.
    The name and all values have whitespace stripped off of them.
    '''
    (name,eq,values) = s.partition('=')
    if not eq:
        raise RuntimeError(f'Bad --foreach argument "{s}":  missing =')

    name = name.strip()
    values = values.strip()

    if values[0] != '[' or values[-1] != ']':
        raise RuntimeError(f'Bad --foreach argument "{s}":  no [] around value-list')

    # Remove the leading and trailing "[]"" characters, then split on ","
    values = values[1:-1].split(',')

    # Trim whitespace off every value in the list, and discard empty values
    values = [v.strip() for v in values]
    values = [v for v in values if len(v) > 0]

    if len(values) == 0:
        raise RuntimeError(f'Bad --foreach argument "{s}":  no values found in list')

    return (name, values)


def check_args(args):
    # Check arguments

    print(f'Reading files from template directory "{args.fromdir}"')
    if not os.path.isdir(args.fromdir):
        print(f'ERROR:  "{args.fromdir}" is not a directory')
        sys.exit(1)


def load_config_file(args) -> dict:
    '''
    Try to load the specified configuration file as either a YAML or JSON
    format file.  If `config_path` is `None` then try to load default
    filenames from within the template directory.

    This function terminates the program if no configuration can be loaded,
    so the function should always return a configuration dictionary.
    '''
    config = None
    config_path = args.config
    if config_path is not None:
        # User has specified a config file.  Try to load as JSON or YAML.
        for mod in [json, yaml]:
            try:
                config = try_load_config_json(config_path)
                break
            except:
                continue

        if config is None:
            print('ERROR:  Couldn\'t load config file "{config_path}" as either a JSON or YAML file')
            sys.exit(1)

    else:
        # No user-specified config file.  Try to load the default config.

        # Try JSON first.
        config_path = os.path.join(args.fromdir, DEFAULT_CONFIGFILE_JSON)
        try:
            config = try_load_config_json(config_path)
        except:
            # Didn't work.  Try YAML second.
            config_path = os.path.join(args.fromdir, DEFAULT_CONFIGFILE_YAML)
            try:
                config = try_load_config_yaml(config_path)
            except:
                # Couldn't load either.  Give up.
                print('ERROR:  Couldn\'t load default JSON or YAML config file')
                sys.exit(1)

    return config


def try_load_config_json(filepath) -> dict:
    with open(filepath) as f:
        return json.load(f)

def try_load_config_yaml(filepath) -> dict:
    with open(filepath) as f:
        return yaml.load(f)


def main(args: Optional[argparse.Namespace]=None) -> None:
    if args is None:
        parser = argparse.ArgumentParser(description='Generate Perturbo '
            'config files and scripts to run one simulation.')
        init_parser(parser)
        args = parser.parse_args()

    print(args)
    check_args(args)

    # Load the config file that says what to do.
    config = load_config_file(args)

    all_vars = set()
    cmdline_vars = {}
    for s in args.set:
        (name, value) = parse_arg_setvar(s)
        if name in all_vars:
            print('ERROR:  variable "{name}" specified multiple times')
            sys.exit(1)

        all_vars.add(name)
        cmdline_vars[name] = value

    foreach_vars = []
    for s in args.foreach:
        name_lst = parse_arg_foreach(s)
        name = name_lst[0]

        if name in all_vars:
            print('ERROR:  variable "{name}" specified multiple times')
            sys.exit(1)

        all_vars.add(name)
        foreach_vars.append(name_lst)

    foreach_generate_target_dir_contents(foreach_vars, args, config)

    print('\nDone!')
