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
    conf.read(file)
    conf.set(section, option, value)
    with open(file,'w',encoding='utf-8') as f:
        conf.write(f)



def read_yaml(file):
    with open(file,'r',encoding='utf-8') as f:
        values = yaml.safe_load(f)
    return values

