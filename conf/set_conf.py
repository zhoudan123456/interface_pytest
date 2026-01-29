import configparser
import pathlib

import yaml

file = pathlib.Path(__file__).parents[0].resolve() / 'server.ini'
conf = configparser.ConfigParser()


def read_conf(section, option):
    conf.read(file)
    values = conf.get(section, option)
    return values


def write_conf(section=None, option=None, value=None):
    if section is not None and option is not None and value is not None:
        conf.read(file)
        conf.set(section, option, value)
        with open(file,'w',encoding='utf-8') as f:
            conf.write(f)



def get_project_root():
    """Get the project root directory"""
    return pathlib.Path(__file__).parents[1].resolve()


def resolve_path(relative_path):
    """Resolve a relative path from the project root directory"""
    if isinstance(relative_path, str):
        # If it's an absolute path, return as is
        if pathlib.Path(relative_path).is_absolute():
            return pathlib.Path(relative_path)
        # Otherwise, resolve from project root
        return get_project_root() / relative_path
    return relative_path


def read_yaml(file):
    """Read YAML file, supports both relative and absolute paths"""
    # Resolve the file path
    file_path = resolve_path(file)
    with open(file_path, 'r', encoding='utf-8') as f:
        values = yaml.safe_load(f)
    return values

def write_yaml(file, data):
    """Write data to a YAML file, supports both relative and absolute paths"""
    # Resolve the file path
    file_path = resolve_path(file)
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)