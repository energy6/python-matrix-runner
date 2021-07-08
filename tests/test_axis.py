# -*- coding: utf-8 -*-
from enum import Enum
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from matrix_runner import Axis


class MyAxisValue(Enum):
    """Test enum for axis values"""
    VALUE1 = ('value1', 'v1')
    VALUE2 = ('value2', 'v2')
    VALUE3 = ('value3', 'v3')


class TestAxis(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):
        cls.axis = Axis('MyAxis', abbrev='a', values=MyAxisValue, desc='Axis for unit test')

    @classmethod
    def tearDownClass(cls):
        del cls.axis

    def test_name(self):
        self.assertEqual('MyAxis', self.axis.name)

    def test_abbrev(self):
        self.assertEqual('a', self.axis.abbrev)

    def test_abbrev_value_error(self):
        with self.assertRaises(ValueError):
            Axis('MyAxis', abbrev='axis', values=MyAxisValue, desc='Axis for unit test')

    def test_desc(self):
        self.assertEqual('Axis for unit test', self.axis.desc)

    @patch('matrix_runner.axis.fnmatch_ex', side_effect=[True, False, True])
    def test_lookup_with_mock(self, mock_fnmatch: MagicMock):
        values = self.axis.lookup('pattern')
        calls = [call(v, 'pattern') for v in MyAxisValue]
        mock_fnmatch.assert_has_calls(calls, any_order=True)
        self.assertEqual(3, mock_fnmatch.call_count)
        self.assertEqual(2, len(values))

    def test_lookup_with_fnmatch_ex(self):
        values = self.axis.lookup('value[23]')
        self.assertListEqual([MyAxisValue.VALUE2, MyAxisValue.VALUE3], values)

    @patch('matrix_runner.Axis.lookup', return_value=[MyAxisValue.VALUE2, MyAxisValue.VALUE3])
    def test_converter_with_mock(self, mock_lookup: MagicMock):
        converter = self.axis.converter()
        self.assertTrue(callable(converter))
        values = converter('value[23]')
        self.assertListEqual([MyAxisValue.VALUE2, MyAxisValue.VALUE3], values)
        mock_lookup.assert_called_once_with('value[23]')

    @patch('matrix_runner.Axis.lookup', return_value=[])
    def test_converter_with_empty_mock(self, mock_lookup: MagicMock):
        converter = self.axis.converter()
        self.assertTrue(callable(converter))
        with self.assertRaises(ValueError):
            converter('value[23]')
        mock_lookup.assert_called_once_with('value[23]')

    def test_converter_lookup(self):
        converter = self.axis.converter()
        self.assertTrue(callable(converter))
        values = converter('value[23]')
        self.assertListEqual([MyAxisValue.VALUE2, MyAxisValue.VALUE3], values)

    def test_getitem(self):
        self.assertTrue(self.axis[0] in MyAxisValue)
        self.assertIsInstance(self.axis[1], MyAxisValue)

    def test_to_list(self):
        values = list(self.axis)
        self.assertListEqual(list(MyAxisValue.__members__.values()), values)
