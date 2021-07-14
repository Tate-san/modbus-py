import json
from json.decoder import JSONDecodeError
from os import read
from typing import Union

def _init_cfg():
    _init_data = {}
    _init_data['devices'] = []
    _init_data['operations'] = []
    with open('config.json', 'w') as writefile:
        json.dump(_init_data, writefile)


def _read_cfg():
    with open('config.json', 'r') as readfile:
        return json.load(readfile)

def _write_cfg(data: json):
    with open('config.json', 'w') as writefile:
        json.dump(data, writefile)

def add_device(name: str, id: int):
    try:
        _read_json= _read_cfg()
        for item in _read_json['devices']:
            if(item['ID'] == id):
                raise BaseException('Device with such ID already exists')
        _read_json['devices'].append({
            'Name': name,
            'ID': id
        })
        _write_cfg(_read_json)
    except JSONDecodeError:
        _init_cfg()
        add_device(name, id)

def add_operation(name: str, id: int):
    try:
        _read_json= _read_cfg()
        for item in _read_json['operations']:
            if(item['ID'] == id):
                raise BaseException('Operation with such ID already exists')
        _read_json['operations'].append({
            'Name': name,
            'ID': id
        })
        _write_cfg(_read_json)
    except JSONDecodeError:
        _init_cfg()
        add_operation(name, id)

def get_operations() -> list:
    _json_read = _read_cfg()
    operations = []
    for item in _json_read['operations']:
        operations.append(item)
    return operations
    

def get_devices() -> list:
    _json_read = _read_cfg()
    devices = []
    for item in _json_read['devices']:
        devices.append(item)
    return devices

def get_count(name: str):
    _json_read = _read_cfg()
    try:
        return _json_read[name][0]['count']
    except Exception as ex:
        print(ex)

if(__name__ == '__main__'):
    print(get_count('drawers'))