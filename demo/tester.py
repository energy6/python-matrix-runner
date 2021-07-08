#!/usr/bin/python
# -*- coding: utf-8 -*-
import platform

from enum import Enum

from matrix_runner import main, matrix_axis, matrix_action, matrix_command, matrix_filter


@matrix_axis("alpha", abbrev="a", desc="First axis")
class MyAlphaAxisValue(Enum):
    """First axis values"""
    VALUE1 = ('value1', 'v1')
    VALUE2 = ('value2', 'v2')
    VALUE3 = ('value3', 'v3')


@matrix_axis("beta", "b", "Second axis")
class MyBetaAxisValue(Enum):
    """Second axis values"""
    VALUE_A = ('valueA', 'vA')
    VALUE_B = ('valueB', 'vB')
    VALUE_C = ('valueC', 'vC')
    VALUE_D = ('valueD', 'vD')


@matrix_axis("gamma", "g", "Third  axis")
class MyGammaAxisValue(Enum):
    """Third axis values"""
    NEGATIVE = (False, 0)
    POSITIVE = (True, 1)


@matrix_command()
def dump_config(config):
    """Command function dumping the config to console."""
    if platform.system() == "Windows":
        return ['powershell', '-Command', f"echo \"{config}\""]
    return ['bash', '-c', f"echo \"{config}\""]


@matrix_action
def dump(config):
    """Dump configuration to console"""
    if config.gamma == MyGammaAxisValue.POSITIVE:
        yield dump_config(config)


@matrix_filter
def value3_with_cd(config):
    """Filter function"""
    return config.alpha.match('value3') and config.beta.match('value[CD]')


if __name__ == "__main__":
    main()
