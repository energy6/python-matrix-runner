# -*- coding: utf-8 -*-

from argparse import ArgumentParser, Namespace
from enum import Enum
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, patch

from parameterized import parameterized

from matrix_runner import Runner, Axis, Action


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
        runner = Runner()

        axis1 = Axis('first', 'f', values=MyAxisValue, desc='First axis')
        axis2 = Axis('second', 's', values=MyAxisValue, desc='Second axis')
        axis3 = Axis('third', 't', values=MyAxisValue, desc='Third axis')
        runner.add_axis([axis1, axis2, axis3])

        action1 = Action('action', MagicMock(), desc='First action')
        runner.add_action(action1)

        runner.run_config = MagicMock()

        runner.run(["--pairwise", "action"])

        self.assertEqual(9, runner.run_config.call_count)

    @parameterized.expand([
        (['--first', 'v1', '--first', 'value3', '--second', 'v2', 'first'],
         {'first': [MyAxisValue.VALUE1, MyAxisValue.VALUE3],
          'second': [MyAxisValue.VALUE2], 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': False, 'silent': False}),
        (['-2', 'first', 'second'],
         {'first': None, 'second': None, 'action': ['first', 'second'],
          'pairwise': True, 'debug': False, 'verbose': False, 'silent': False}),
        (['--debug', 'first'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': True, 'verbose': False, 'silent': False}),
        (['--verbose', 'first'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': True, 'silent': False}),
        (['--silent', 'first'],
         {'first': None, 'second': None, 'action': ['first'],
          'pairwise': False, 'debug': False, 'verbose': False, 'silent': True})
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
                              'pairwise': False, 'debug': False, 'verbose': False, 'silent': False}, vars(result))

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
