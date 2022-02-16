# -*- coding: utf-8 -*-

import os

from contextlib import contextmanager
from enum import Enum
from tempfile import gettempdir
from unittest import TestCase
from unittest.mock import MagicMock

from colors import strip_color

from matrix_runner import Axis, Action
from matrix_runner import main
from tests._helper import captured_output


class MyAlphaAxisValue(Enum):
    """Enum with axis values"""
    VALUE1 = ('value1', 'v1')
    VALUE2 = ('value2', 'v2')
    VALUE3 = ('value3', 'v3')


class MyBetaAxisValue(Enum):
    """Enum with axis values"""
    VALUE_A = ('valueA', 'vA')
    VALUE_B = ('valueB', 'vB')
    VALUE_C = ('valueC', 'vC')
    VALUE_D = ('valueD', 'vD')


class TestMain(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    axes = None
    actions = None

    @classmethod
    def setUpClass(cls):
        cls.axes = [
            Axis('alpha', 'f', values=MyAlphaAxisValue, desc='First axis'),
            Axis('beta', 's', values=MyBetaAxisValue, desc='Second axis')
        ]
        # noinspection PyTypeChecker
        cls.actions = [
            Action('primary', MagicMock(return_value=[MagicMock(return_value=MagicMock())]), desc='First action'),
            Action('secondary', MagicMock(return_value=[MagicMock(return_value=MagicMock())]), desc='Second action')
        ]

    @classmethod
    def tearDownClass(cls):
        del cls.axes
        del cls.actions

    def test_main_usage(self):
        with captured_output() as (stdout, _):
            with self.assertRaises(SystemExit):
                main(['--help'])
            self.assertIn("usage:", stdout.getvalue())

    def test_main_primary(self):
        with captured_output() as (stdout, _):
            with self.assertRaises(SystemExit):
                main(['primary'])
            self.assertIn("Matrix Summary", stdout.getvalue())
            self.assertRegex(strip_color(stdout.getvalue()),
                             "(value[1-3]\\s+value[A-D]\\s+success\\s+\\(skip\\)\\n){12}")

    def test_main_out_of_tree(self):
        @contextmanager
        def tempdir():
            cwd = os.getcwd()
            os.chdir(gettempdir())
            try:
                yield
            finally:
                os.chdir(cwd)

        with captured_output() as (_, stderr):
            with self.assertRaises(SystemExit), tempdir():
                main(['primary'])
            self.assertRegex(strip_color(stderr.getvalue()), "located in the current working")
            self.assertRegex(strip_color(stderr.getvalue()), "Expected working directory")
            self.assertRegex(strip_color(stderr.getvalue()), "Actual working directory")
