# -*- coding: utf-8 -*-

from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock

from colors import strip_color

from matrix_runner.action import Action
from matrix_runner.preferences import Preferences
from matrix_runner.report import ReportFilter

from tests._helper import captured_output


class TestAction(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):
        # Assure well-known fallback preferences are used
        cls.prefs = Preferences.instance
        Preferences.instance = Preferences(system=Path(), user=Path(), local=Path())

    @classmethod
    def tearDownClass(cls):
        Preferences.instance = cls.prefs

    def test_summary(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")

        # AND annotating a function as summary
        @action.summary
        def summary(_):  # pylint: disable=unused-argument
            ...

        # THEN the function is registered as the summary function
        self.assertEqual(summary, action._get_summary)

    def test_get_instances(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        # WHEN retrieving all action instances
        actions = Action.get_instances()
        # THEN the list contains the action
        self.assertListEqual([action], list(actions))

    def test_get_instances_deleted(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        self.assertIsInstance(action, Action)
        # WHEN deleting the action
        del action
        # ... AND retrieving all action instances
        actions = Action.get_instances()
        # THEN the list is empty
        self.assertListEqual([], list(actions))

    def test_name(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        # THEN the name property returns the given one
        self.assertEqual("action", action.name)

    def test_desc(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        # THEN the desc property returns the given one
        self.assertEqual("description for action", action.desc)

    def test_get_summary_success(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        # ... AND a list of mock'ed successful results
        rmock = MagicMock()
        type(rmock).success = PropertyMock(return_value=True)
        results = [rmock, rmock]
        # THEN the summary is success
        self.assertEqual("success", strip_color(action.get_summary(results)))

    def test_get_summary_failed(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        # ... AND a list of mock'ed results
        rsmock = MagicMock()
        type(rsmock).success = PropertyMock(return_value=True)
        rfmock = MagicMock()
        type(rfmock).success = PropertyMock(return_value=False)
        results = [rsmock, rfmock, rsmock]
        # THEN the summary is success
        self.assertEqual("\x1b[1;31mFAILED\x1b[0m", action.get_summary(results))

    def test_get_summary_skip(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        # THEN the summary for an empty list of results is skip
        self.assertEqual("\x1b[33m(skip)\x1b[0m", action.get_summary([]))

    def test_get_summary_from_reports(self):
        action = Action("action", MagicMock(), "description for action")

        report_mock1 = type('ReportWithSummaryMock', (MagicMock, ReportFilter.Summary,), {})()
        type(report_mock1).summary = PropertyMock(return_value=(8, 8))
        report_mock2 = type('ReportWithSummaryMock', (MagicMock, ReportFilter.Summary,), {})()
        type(report_mock2).summary = PropertyMock(return_value=(42, 42))

        result1 = MagicMock()
        type(result1).success = PropertyMock(return_value=True)
        type(result1).test_report = PropertyMock(return_value=report_mock1)
        result2 = MagicMock()
        type(result2).success = PropertyMock(return_value=True)
        type(result2).test_report = PropertyMock(return_value=report_mock2)

        summary = action.get_summary([result1, result2])

        self.assertEqual("\x1b[32m50/50\x1b[0m", summary)

    def test_get_summary_from_reports_with_failures(self):
        action = Action("action", MagicMock(), "description for action")

        report_mock1 = type('ReportWithSummaryMock', (MagicMock, ReportFilter.Summary,), {})()
        type(report_mock1).summary = PropertyMock(return_value=(6, 8))
        report_mock2 = type('ReportWithSummaryMock', (MagicMock, ReportFilter.Summary,), {})()
        type(report_mock2).summary = PropertyMock(return_value=(42, 42))

        result1 = MagicMock()
        type(result1).success = PropertyMock(return_value=True)
        type(result1).test_report = PropertyMock(return_value=report_mock1)
        result2 = MagicMock()
        type(result2).success = PropertyMock(return_value=True)
        type(result2).test_report = PropertyMock(return_value=report_mock2)

        summary = action.get_summary([result1, result2])

        self.assertEqual("\x1b[33m48/50\x1b[0m", summary)

    def test_get_summary_mixed_with_reports(self):
        action = Action("action", MagicMock(), "description for action")

        report_mock1 = type('ReportWithSummaryMock', (MagicMock, ReportFilter.Summary,), {})()
        type(report_mock1).summary = PropertyMock(return_value=(42, 42))
        report_mock2 = type('ReportMock', (MagicMock, ReportFilter.Result,), {})()

        result1 = MagicMock()
        type(result1).success = PropertyMock(return_value=True)
        type(result1).test_report = PropertyMock(return_value=report_mock1)
        result2 = MagicMock()
        type(result2).success = PropertyMock(return_value=True)
        type(result2).test_report = PropertyMock(return_value=report_mock2)

        summary = action.get_summary([result1, result2])

        self.assertEqual("\x1b[32m42/42\x1b[0m", summary)

    def test_get_summary_custom(self):
        # GIVEN a mock'ed action
        action = Action("action", MagicMock(), "description for action")
        # ... AND a custom summary function
        action._get_summary = MagicMock(return_value="%(purple)ssummary")
        # ... AND a list of mock'ed successful results
        rmock = MagicMock()
        type(rmock).success = PropertyMock(return_value=True)
        results = [rmock, rmock]
        # THEN the summary is the custom return value
        self.assertEqual("\x1b[35msummary\x1b[0m", action.get_summary(results))
        # ... AND the custom summary function was called
        action._get_summary.assert_called_once_with(results)

    def test_call_with_config(self):
        # GIVEN a mock'ed action
        config = MagicMock()
        expected_results = [MagicMock(name='result1'), MagicMock(name='result2')]
        cmds = [
            MagicMock(name='cmd1', return_value=expected_results[0]),
            MagicMock(name='cmd2', return_value=expected_results[1])
        ]
        action_mock = MagicMock(return_value=cmds)
        action = Action("action",
                        lambda c: action_mock(c),  # pylint: disable=unnecessary-lambda
                        "description for action")

        # WHEN the action is called
        results = action(config)

        # THEN the results are as expected
        self.assertEqual(expected_results, results)
        # ... AND the action has been called
        action_mock.assert_called_once_with(config)
        # ... AND all commands have been called once
        cmds[0].assert_called_once_with()
        cmds[1].assert_called_once_with()

    def test_call_with_result(self):
        # GIVEN a mock'ed action
        config = MagicMock()
        expected_results = [MagicMock(name='result1'), MagicMock(name='result2')]
        cmds = [
            MagicMock(name='cmd1', return_value=expected_results[0]),
            MagicMock(name='cmd2', return_value=expected_results[1])
        ]
        action_mock = MagicMock(return_value=cmds)
        action = Action("action",
                        lambda c, r: action_mock(c, r),  # pylint: disable=unnecessary-lambda
                        "description for action")

        # WHEN the action is called
        results = action(config)

        # THEN the results are as expected
        self.assertEqual(expected_results, results)
        # ... AND the action has been called
        action_mock.assert_called_once_with(config, results)
        # ... AND all commands have been called once
        cmds[0].assert_called_once_with()
        cmds[1].assert_called_once_with()

    def test_call_with_exception(self):
        # GIVEN a mock'ed action
        config = MagicMock()
        expected_results = [MagicMock(name='result1')]
        cmds = [
            MagicMock(name='cmd1', return_value=expected_results[0]),
            MagicMock(name='cmd2')
        ]

        # ... WITH a generator function raising an exception
        def fn(_):
            yield cmds[0]
            raise RuntimeError('Runtime error in action function!')
            # noinspection PyUnreachableCode
            yield cmds[1]  # pylint: disable=unreachable

        action_mock = MagicMock(side_effect=fn)
        action = Action("action",
                        lambda c: action_mock(c),  # pylint: disable=unnecessary-lambda
                        "description for action")

        # WHEN the action is called
        with captured_output() as (_, stderr):
            results = action(config)

        # THEN the exception is logged
        self.assertRegex(stderr.getvalue(), "Runtime error in action function!")
        # ... AND the results are as expected
        self.assertEqual(expected_results[0], results[0])
        self.assertFalse(results[1].success)
        # ... AND the action has been called
        action_mock.assert_called_once_with(config)
        # ... AND the commands have been called once up to the exception
        cmds[0].assert_called_once_with()
        cmds[1].assert_not_called()

    def test_call_with_extra_args(self):
        # GIVEN two mock'ed actions
        config = MagicMock()
        args = MagicMock()
        expected_results = [MagicMock(name='result1'), MagicMock(name='result2')]
        cmds = [
            MagicMock(name='cmd1', return_value=expected_results[0]),
            MagicMock(name='cmd2', return_value=expected_results[1])
        ]
        action_mock = MagicMock(return_value=cmds)
        action1 = Action("action",
                        lambda c, extra_args: action_mock(c, extra_args),  # pylint: disable=unnecessary-lambda
                        "description for action")
        action2 = Action("action",
                        lambda c, r, extra_args: action_mock(c, r, extra_args),  # pylint: disable=unnecessary-lambda
                        "description for action")

        # WHEN the first action is called
        results = action1(config, extra_args=args)
        # THEN the results are as expected
        self.assertEqual(expected_results, results)
        # ... AND the action has been called
        action_mock.assert_called_once_with(config, args)
        # ... AND all commands have been called once
        cmds[0].assert_called_once_with()
        cmds[1].assert_called_once_with()

        action_mock.reset_mock()
        cmds[0].reset_mock()
        cmds[1].reset_mock()        

        # WHEN the second action is called
        results = action2(config, extra_args=args)
        # THEN the results are as expected
        self.assertEqual(expected_results, results)
        # ... AND the action has been called
        action_mock.assert_called_with(config, expected_results, args)
        # ... AND all commands have been called once
        cmds[0].assert_called_with()
        cmds[1].assert_called_with()
