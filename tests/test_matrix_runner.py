# -*- coding: utf-8 -*-
from enum import Enum, EnumMeta
from typing import Iterable
from unittest import TestCase
from unittest.mock import MagicMock

from matrix_runner import matrix_axis, matrix_action, matrix_command, Axis, Action, Command


class TestMatrixRunner(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    def test_matrix_axis(self):
        # GIVEN an enum class decorated as matrix axis
        @matrix_axis("axis", "a", "A matrix axis.")
        class MyAxisValue(Enum):
            VALUE1 = ('value1', 'v1')
            VALUE2 = ('value2', 'v2')
            VALUE3 = ('value3', 'v3')

        # THEN the class is used as an Axis
        self.assertIs(EnumMeta, type(MyAxisValue))
        self.assertTrue(hasattr(MyAxisValue, 'axis'))
        self.assertIs(Axis, type(MyAxisValue.axis))                # pylint: disable=no-member
        self.assertEqual("axis", MyAxisValue.axis.name)            # pylint: disable=no-member
        self.assertEqual("a", MyAxisValue.axis.abbrev)             # pylint: disable=no-member
        self.assertEqual("A matrix axis.", MyAxisValue.axis.desc)  # pylint: disable=no-member

    def test_matrix_action(self):
        # GIVEN some mocks
        config_mock = MagicMock()
        action_mock = MagicMock(return_value=[])

        # ... AND a function decorated as matrix action
        @matrix_action
        def action(config):
            return action_mock(config)

        # THEN an Action instance has been created from the function
        self.assertIsInstance(action, Action)
        # ... AND this instance is bound to the function
        self.assertIsInstance(action._fn(config_mock), Iterable)
        action_mock.assert_called_once_with(config_mock)

    def test_matrix_command(self):
        # GIVEN some mocks
        config_mock = MagicMock()
        cmdline = ["cmd", "arg1", "arg2"]
        cmd_args = ["arg1", "arg2"]
        cmd_kwargs = {"arg3": 42}
        cmd_mock = MagicMock(return_value=cmdline)

        # ... AND a function decorated as matrix command
        @matrix_command()
        def command(config, *args, **kwargs):
            return cmd_mock(config, *args, **kwargs)

        # WHEN calling the command with arguments
        cmd = command(config_mock, *cmd_args, **cmd_kwargs)

        # THEN a Command object is retrieved
        self.assertIsInstance(cmd, Command)
        # ... AND the function has not been called
        cmd_mock.assert_not_called()
        # ... AND the Command object is bound to the function
        self.assertListEqual(cmd._fn(), cmdline)
        cmd_mock.assert_called_once_with(config_mock, *cmd_args, **cmd_kwargs)
