#!/usr/bin/python
# -*- coding: utf-8 -*-
import platform

from enum import Enum

from matrix_runner import main, matrix_axis, matrix_action, matrix_command


@matrix_axis("alpha", "a", "A configuration axis")
class MyAlphaAxisValue(Enum):
    """Alpha axis values"""
    VALUE1 = ('value1', 'v1')
    VALUE2 = ('value2', 'v2')
    VALUE3 = ('value3', 'v3')


@matrix_action
def dump(config, results):
    """Dump configuration to console"""
    yield dump_config(config, 'Hello', 'World')
    print(results[0].command.config)


@matrix_command()
def dump_config(config, *args):
    """Dump arguments"""
    if platform.system() == "Windows":
        return ['powershell', '-Command', f"echo \"{' '.join(args)}: {config}\""]
    return ['bash', '-c', f"echo \"{' '.join(args)}: {config}\""]


if __name__ == "__main__":
    main()
