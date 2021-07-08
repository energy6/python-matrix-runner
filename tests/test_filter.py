# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock

from matrix_runner.filter import Filter


class TestFilter(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    def test_match_true(self):
        # GIVEN two mock'ed filters (one that applies)
        fnmock1 = MagicMock(return_value=False)
        fnmock2 = MagicMock(return_value=True)
        filter1 = Filter(fnmock1)  # pylint: disable=unused-variable
        filter2 = Filter(fnmock2)  # pylint: disable=unused-variable
        # ... AND a mock'ed config
        config_mock = MagicMock()

        # WHEN calling match
        result = Filter.match(config_mock)

        # THEN the result should be True
        self.assertTrue(result)
        # ... AND at least the matching filter function has been called once
        fnmock2.assert_called_once_with(config_mock)
        # ... AND the other not matching filter function might have not been
        #         called due to boolean shortcut

    def test_match_false(self):
        # GIVEN two mock'ed filters (none does apply)
        fnmock1 = MagicMock(return_value=False)
        fnmock2 = MagicMock(return_value=False)
        filter1 = Filter(fnmock1)  # pylint: disable=unused-variable
        filter2 = Filter(fnmock2)  # pylint: disable=unused-variable
        # ... AND a mock'ed config
        config_mock = MagicMock()

        # WHEN calling match
        result = Filter.match(config_mock)

        # THEN the result should be False
        self.assertFalse(result)
        # ... AND both filter function has been called once
        fnmock1.assert_called_once_with(config_mock)
        fnmock2.assert_called_once_with(config_mock)

    def test_get_instances(self):
        # GIVEN two mock'ed filters (none does apply)
        filter1 = Filter(MagicMock())
        filter2 = Filter(MagicMock())

        # WHEN retrieving all filter instances
        filters = Filter.get_instances()

        # THEN the list contains both filters
        self.assertCountEqual([filter1, filter2], list(filters))

    def test_get_instances_del(self):
        # GIVEN two mock'ed filters (none does apply)
        filter1 = Filter(MagicMock())
        filter2 = Filter(MagicMock())

        # ... AND prematurely deleting one of them
        del filter1

        # WHEN retrieving all filter instances
        filters = Filter.get_instances()

        # THEN the list contains only the remaining filter
        self.assertListEqual([filter2], list(filters))
