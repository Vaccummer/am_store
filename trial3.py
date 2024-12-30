from am_store.common_tools import *
from ruamel.yaml import YAML as ryaml
dict_f = yml.read('launcher_cfg_new.yaml')
import json

with open('example.yaml', 'r', encoding='utf-8') as f:
    data = ryaml.load(f, ryaml.RoundTripLoader)
