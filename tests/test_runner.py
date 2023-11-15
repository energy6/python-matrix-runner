# -*- coding: utf-8 -*-
import logging
from argparse import ArgumentParser, Namespace
from enum import Enum
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, patch, call, ANY

import matrix_runner
from parameterized import parameterized

from matrix_runner import Runner, Axis, Action
from matrix_runner.config import Config
from matrix_runner.runner import Slice
from tests._helper import captured_output


class MyAxisValue(Enum):
    """Test axis values"""
    VALUE1 = ('value1', 'v1')
    VALUE2 = ('value2', 'v2')
    VALUE3 = ('value3', 'v3')


class MyBoolAxisValue(Enum):
    """Test axis values"""
    NEGATIVE = (False, 0)
    POSITIVE = (True, 1)


class TestRunner(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    def test_add_axis_single(self):
        runner = Runner()
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        runner.add_axis(axis1)
        runner.add_axis(axis2)
        self.assertDictEqual({axis1.name: axis1, axis2.name: axis2}, dict(runner.axes))

    def test_add_axis_multiple(self):
        runner = Runner()
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        runner.add_axis([axis1, axis2])
        self.assertDictEqual({axis1.name: axis1, axis2.name: axis2}, dict(runner.axes))

    def test_add_axis_twice(self):
        runner = Runner()
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        runner.add_axis(axis1)
        with self.assertRaises(ValueError):
            runner.add_axis(axis1)

    def test_add_axis_typeerror(self):
        runner = Runner()
        with self.assertRaises(TypeError):
            runner.add_axis('first')
        with self.assertRaises(TypeError):
            runner.add_axis(['first', 'second'])

    def test_add_action_single(self):
        runner = Runner()
        action1 = Action('first', MagicMock(), desc='First action')
        action2 = Action('second', MagicMock(), desc='Second action')
        runner.add_action(action1)
        runner.add_action(action2)
        self.assertDictEqual({action1.name: action1, action2.name: action2}, dict(runner.actions))

    def test_add_action_multiple(self):
        runner = Runner()
        action1 = Action('first', MagicMock(), desc='First action')
        action2 = Action('second', MagicMock(), desc='Second action')
        runner.add_action([action1, action2])
        self.assertDictEqual({action1.name: action1, action2.name: action2}, dict(runner.actions))

    def test_add_action_twice(self):
        runner = Runner()
        action1 = Action('first', MagicMock(), desc='First action')
        runner.add_action(action1)
        with self.assertRaises(ValueError):
            runner.add_action(action1)

    def test_add_action_typeerror(self):
        runner = Runner()
        with self.assertRaises(TypeError):
            runner.add_action('first')
        with self.assertRaises(TypeError):
            runner.add_action(['first', 'second'])

    def test_run(self):
        runner = Runner()

        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        axis3 = Axis('third', 't', values=MyAxisValue, desc='Third axis')
        runner.add_axis([axis1, axis2, axis3])

        action1 = Action('action', MagicMock(), desc='First action')
        runner.add_action(action1)

        runner.run_config = MagicMock()

        runner.run(["action"])

        self.assertEqual(27, runner.run_config.call_count)

    def test_run_with_pairwise(self):
        # GIVEN a Runner with mocked run_config method
        runner = Runner()
        runner.run_config = MagicMock()

        # ... and three axes with three values each
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        axis3 = Axis('third', 't', values=MyAxisValue, desc='Third axis')
        runner.add_axis([axis1, axis2, axis3])

        # ... and a single action
        action1 = Action('action', MagicMock(), desc='First action')
        runner.add_action(action1)

        # WHEN running the pairwise reduction
        runner.run(["--pairwise", "action"])

        # THEN only nine out of 27 configurations are ran
        expected_calls = [
            call(ANY, Config(first=MyAxisValue.VALUE1, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE1), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE2, second=MyAxisValue.VALUE2, third=MyAxisValue.VALUE1), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE3, second=MyAxisValue.VALUE3, third=MyAxisValue.VALUE1), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE3, second=MyAxisValue.VALUE2, third=MyAxisValue.VALUE2), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE2, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE2), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE1, second=MyAxisValue.VALUE3, third=MyAxisValue.VALUE2), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE1, second=MyAxisValue.VALUE2, third=MyAxisValue.VALUE3), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE2, second=MyAxisValue.VALUE3, third=MyAxisValue.VALUE3), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE3, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE3), ANY)
        ]
        runner.run_config.assert_has_calls(expected_calls)
        self.assertEqual(runner.run_config.call_count, len(expected_calls))

    def test_slice(self):
        testee = Slice('1/2')
        self.assertEqual(testee.numerator, 1)
        self.assertEqual(testee.denominator, 2)

        with self.assertRaises(ValueError):
            Slice('a')

        with self.assertRaises(ValueError):
            Slice('3/2')

        with self.assertRaises(ValueError):
            Slice('0/2')

        with self.assertRaises(ValueError):
            Slice('1/0')

        with self.assertRaises(ValueError):
            Slice('-1/-1')

    def test_run_with_slice(self):
        # GIVEN a Runner with mocked run_config method
        runner = Runner()
        runner.run_config = MagicMock()

        # ... with three axes and three values each
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        axis3 = Axis('third', 't', values=MyAxisValue, desc='Third axis')
        runner.add_axis([axis1, axis2, axis3])

        # ... and a single action
        action1 = Action('action', MagicMock(), desc='First action')
        runner.add_action(action1)

        # WHEN running the first out of five slices
        runner.run(['--slice', '1/5', 'action'])

        # THEN the the first six permutations are ran
        expected_calls = [
            call(ANY, Config(first=MyAxisValue.VALUE1, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE1), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE1, second=MyAxisValue.VALUE2, third=MyAxisValue.VALUE3), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE2, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE2), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE2, second=MyAxisValue.VALUE3, third=MyAxisValue.VALUE1), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE3, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE3), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE3, second=MyAxisValue.VALUE3, third=MyAxisValue.VALUE2), ANY)
        ]
        runner.run_config.assert_has_calls(expected_calls)
        self.assertEqual(runner.run_config.call_count, len(expected_calls))

        # WHEN running the last out of five slices
        runner.run_config.reset_mock()
        runner.run(['--slice', '5/5', 'action'])

        # THEN the last five permutations are ran
        expected_calls = [
            call(ANY, Config(first=MyAxisValue.VALUE1, second=MyAxisValue.VALUE2, third=MyAxisValue.VALUE2), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE2, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE1), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE2, second=MyAxisValue.VALUE2, third=MyAxisValue.VALUE3), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE3, second=MyAxisValue.VALUE1, third=MyAxisValue.VALUE2), ANY),
            call(ANY, Config(first=MyAxisValue.VALUE3, second=MyAxisValue.VALUE3, third=MyAxisValue.VALUE1), ANY)
        ]
        runner.run_config.assert_has_calls(expected_calls)
        self.assertEqual(runner.run_config.call_count, len(expected_calls))

    def test_run_with_empty_slice(self):
        # GIVEN a Runner with mocked run_config method
        runner = Runner()
        runner.run_config = MagicMock()

        # ... with three axes and three values each
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        axis3 = Axis('third', 't', values=MyAxisValue, desc='Third axis')
        runner.add_axis([axis1, axis2, axis3])

        # ... and a single action
        action1 = Action('action', MagicMock(), desc='First action')
        runner.add_action(action1)

        with captured_output() as (_, stderr):
            logging.basicConfig(force=True)

            # WHEN running more slices than available combinations
            runner.run(['--slice', '28/28', 'action'])

        # THEN  no combination is ran
        runner.run_config.assert_not_called()

        # ... and a warning is emitted to stderr
        self.assertIn("Deviding 27 combination into 28 slices results in empty runs!", stderr.getvalue())

    def test_slice_shadowed(self):
        # GIVEN a Runner with mocked run_config method
        runner = Runner()
        runner.run_config = MagicMock()

        # ... with an axis called slice
        slice_axis = Axis('slice', 's', values=MyAxisValue, desc='Slice axis')
        runner.add_axis([slice_axis])

        # ... and a single action
        action1 = Action('action', MagicMock(), desc='First action')
        runner.add_action(action1)

        with captured_output() as (_, stderr):
            logging.basicConfig(force=True)

            # WHEN running the action
            runner.run(['action'])

        # THEN a warning is emitted to stderr
        self.assertIn("Axis slice shadows built-in --slice flag!", stderr.getvalue())

    @parameterized.expand([
        (['--first', 'v1', '--first', 'value3', '--second', 'v2', 'first'],
         {'first': [MyAxisValue.VALUE1, MyAxisValue.VALUE3],
          'second': [MyAxisValue.VALUE2], 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': False, 'silent': False,
          'slice': None, 'extra_args': None, 'first_args': None, 'second_args': None}),
        (['-2', 'first', 'second'],
         {'first': None, 'second': None, 'action': ['first', 'second'],
          'pairwise': True, 'debug': False, 'verbose': False, 'silent': False,
          'slice': None, 'extra_args': None, 'first_args': None, 'second_args': None}),
        (['--debug', 'first'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': True, 'verbose': False, 'silent': False,
          'slice': None, 'extra_args': None, 'first_args': None, 'second_args': None}),
        (['--verbose', 'first'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': True, 'silent': False,
          'slice': None, 'extra_args': None, 'first_args': None, 'second_args': None}),
        (['--silent', 'first'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': False, 'silent': True,
          'slice': None, 'extra_args': None, 'first_args': None, 'second_args': None}),
        (['--slice', '1/2', 'first'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': False, 'silent': False,
          'slice': matrix_runner.runner.Slice('1/2'),
          'extra_args': None, 'first_args': None, 'second_args': None}),
        (['first', '--extra-args="--extra1"', '--first-args="--extra2"', '--second-args="--extra3"'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': False, 'silent': False,
          'slice': None, 'extra_args': ['--extra1'], 'first_args': ['--extra2'], 'second_args': ['--extra3']})
    ])
    def test_arg_parser(self, argv, args):
        # Given a new Runner object
        runner = Runner()

        # ... with two matrix axes
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        runner.add_axis([axis1, axis2])

        # ... and two actions
        actions = {'first': Action('first', MagicMock(), desc='First action'),
                   'second': Action('second', MagicMock(), desc='Second action')}
        runner.add_action(actions.values())

        args['action'] = [actions[a] for a in args['action']]

        # Then the _arg_parser property shall be an ArgumentParser instance
        parser = runner._arg_parser
        self.assertIsInstance(parser, ArgumentParser)

        # ... which returns the expected Namespace object
        result = parser.parse_args(argv)
        self.assertDictEqual(args, vars(result))

    def test_arg_parser_with_bool(self):
        # Given a new Runner object
        runner = Runner()

        # ... with two matrix axes
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyBoolAxisValue, desc='Second axis')
        runner.add_axis([axis1, axis2])

        # ... and two actions
        actions = {'first': Action('first', MagicMock(), desc='First action'),
                   'second': Action('second', MagicMock(), desc='Second action')}
        runner.add_action(actions.values())

        # Then the _arg_parser property shall be an ArgumentParser instance
        parser = runner._arg_parser
        self.assertIsInstance(parser, ArgumentParser)

        # ... which returns the expected Namespace object
        result = parser.parse_args(['-s', 'True', 'first'])
        self.assertDictEqual({'first': None, 'second': [MyBoolAxisValue.POSITIVE], 'action': [actions['first']],
                              'pairwise': False, 'debug': False, 'verbose': False, 'silent': False, 'slice': None,
                              'extra_args': None, 'first_args': None, 'second_args': None}, vars(result))

    def test_parse_args(self):
        # Given a new Runner object
        runner = Runner()

        # ... with two matrix axes
        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        runner.add_axis([axis1, axis2])

        # ... and mocking the real _arg_parser property
        with patch('matrix_runner.runner.Runner._arg_parser', new_callable=PropertyMock) as arg_parser_mock:
            arg_parser_mock.return_value = MagicMock()
            arg_parser_mock.return_value.parse_args = \
                MagicMock(return_value=Namespace(first=None, second=[MyAxisValue.VALUE2]))

            # When calling the parse_args method
            # ... with a value for axis 'second' only
            args = runner._parse_args(['--second', 'value2'])

            # Then the return value shall contain
            # ... all possible values for axis 'first'
            expected_args = {'first': axis1.values, 'second': [MyAxisValue.VALUE2]}
            self.assertDictEqual(expected_args, vars(args))
