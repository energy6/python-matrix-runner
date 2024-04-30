# -*- coding: utf-8 -*-

import logging
import os
import platform

from pathlib import Path
from tempfile import NamedTemporaryFile
from textwrap import dedent
from unittest import TestCase, mock
from unittest.mock import MagicMock, call, ANY, DEFAULT, NonCallableMagicMock

from matrix_runner._helper import partial_with_inspect
from matrix_runner.command import Command, Result
from matrix_runner.runner import RunnerApplication

from tests._helper import captured_output


def is_windows():
    """Helper function to check for Windows OS"""
    return platform.system() == "Windows"


class TestCommand(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    def test_call(self):
        # GIVEN a Command with mock'ed function
        cmdline = ['cmd', 'line']
        fnmock = MagicMock(__name__='fnmock', return_value=cmdline)
        cmd = Command(fnmock)

        # ... AND mock'ed _execute function
        with mock.patch('matrix_runner.command.Command._execute') as exec_mock:
            # WHEN calling the command
            result = cmd()

            # THEN the command function has been called
            fnmock.assert_called_once()
            # ... AND the command line has been passed to execute function
            exec_mock.assert_called_once_with(cmdline, ANY)
            # ... AND the result contains valid data
            self.assertEqual(result.command, cmd)
            self.assertEqual(result.cmdline, cmdline)

    def test_getattr(self):
        # GIVEN a Command with a function bound to some arguments
        cmdline = ['cmd', 'line']
        fnmock = MagicMock(__name__='fnmock', return_value=cmdline)
        cmd = Command(partial_with_inspect(fnmock, arg2=42))

        # WHEN retrieving the argument
        # THEN the bound value is returned
        self.assertEqual(cmd.arg2, 42)

    def test_resolve_cmdline(self):
        # GIVEN a Command with mock'ed function
        cmd = Command(MagicMock)
        # ... AND mock'ed utility functions
        resolve = MagicMock(side_effect=lambda v: v)
        with mock.patch('shutil.which', return_value="python") as which, \
             mock.patch('pathlib.Path.resolve',
                        lambda s: resolve(s)):  # pylint: disable=unnecessary-lambda

            # WHEN resolving an assumed command line
            resolved = cmd._resolve_cmdline(["python", Path("test.py"), 42])

            # THEN the command has been passed to shutil.which
            which.assert_called_once_with('python')
            # ... AND the Path has been resolved
            resolve.assert_called_once_with(Path('test.py'))
            # ... AND all elements are resolved to strings
            self.assertListEqual(["python", "test.py", "42"], resolved)

    def test_is_success_default(self):
        # GIVEN a Command with mock'ed function and default exit_code
        cmd = Command(MagicMock)

        # WHEN/THEN 0 denotes success
        self.assertTrue(cmd._is_success(0))
        # WHEN/THEN 1 denotes failure
        self.assertFalse(cmd._is_success(1))
        # WHEN/THEN -1 denotes failure
        self.assertFalse(cmd._is_success(-1))

    def test_is_success_range(self):
        # GIVEN a Command with mock'ed function and exit_code as a range
        cmd = Command(MagicMock, exit_code=range(0, 2))

        # WHEN/THEN 0 denotes success
        self.assertTrue(cmd._is_success(0))
        # WHEN/THEN 1 denotes success
        self.assertTrue(cmd._is_success(1))
        # WHEN/THEN 2 denotes failure
        self.assertFalse(cmd._is_success(2))
        # WHEN/THEN -1 denotes failure
        self.assertFalse(cmd._is_success(-1))

    def test_is_success_list(self):
        # GIVEN a Command with mock'ed function and exit_code as a list
        cmd = Command(MagicMock, exit_code=[127, 4711])

        # WHEN/THEN 127 denotes success
        self.assertTrue(cmd._is_success(127))
        # WHEN/THEN 4711 denotes success
        self.assertTrue(cmd._is_success(4711))
        # WHEN/THEN 0 denotes failure
        self.assertFalse(cmd._is_success(0))
        # WHEN/THEN 126 denotes failure
        self.assertFalse(cmd._is_success(126))
        # WHEN/THEN 128 denotes failure
        self.assertFalse(cmd._is_success(128))
        # WHEN/THEN 4710 denotes failure
        self.assertFalse(cmd._is_success(4710))
        # WHEN/THEN 4712 denotes failure
        self.assertFalse(cmd._is_success(4712))

    def test_is_success_func_true(self):
        func = MagicMock(return_value=True)
        cmd = Command(MagicMock, exit_code=func)
        self.assertTrue(cmd._is_success(0))
        func.assert_called_once_with(0)

    def test_is_success_func_false(self):
        func = MagicMock(return_value=False)
        cmd = Command(MagicMock, exit_code=func)
        self.assertFalse(cmd._is_success(1))
        func.assert_called_once_with(1)

    def test_execute_default(self):
        cmdline = ['cmd', 'line', 'args']
        cmdline_resolved = ['resolved_cmd', 'line', 'args']

        # GIVEN internal Command functions mock'ed
        with mock.patch('matrix_runner.command.Command._popen', new_callable=MagicMock) as popen_mock,\
             mock.patch('matrix_runner.command.Command._resolve_cmdline', new_callable=MagicMock) as resolve_mock,\
             mock.patch('matrix_runner.command.FileLock', new_callable=MagicMock) as lock_mock,\
             mock.patch('matrix_runner.command.sleep', new_callable=MagicMock) as sleep_mock:
            # ... AND a Command object with default parameters is used
            cmd = Command(MagicMock)
            # ... AND using mock'ed result
            result_mock = MagicMock()
            # ... AND letting the execution return exit code 0
            popen_mock.return_value = 0
            # ... AND letting the resolver return a modified command line
            resolve_mock.return_value = cmdline_resolved

            # WHEN executing a given command line
            cmd._execute(cmdline, result_mock)

            # THEN the result is success
            self.assertTrue(result_mock.success)
            # ... AND the resolver got called once with the original command line
            resolve_mock.assert_called_once_with(cmdline)
            # ... AND the executor got called once with the resolved command line and default parameters
            popen_mock.assert_called_once_with(cmdline_resolved, result_mock, needs_shell=False, encoding='utf-8',
                                               timeout=None, extra=ANY)
            # ... AND no FileLock has been acquired
            lock_mock.assert_not_called()
            # ... AND no sleep has been issued
            sleep_mock.assert_not_called()

    def test_execute_fail_with_params(self):
        cmdline = ['cmd', 'line', 'args']
        cmdline_resolved = ['resolved_cmd', 'line', 'args']

        # GIVEN internal Command functions mock'ed
        with mock.patch('matrix_runner.command.Command._popen', new_callable=MagicMock) as popen_mock,\
             mock.patch('matrix_runner.command.Command._resolve_cmdline', new_callable=MagicMock) as resolve_mock,\
             mock.patch('matrix_runner.command.FileLock', new_callable=MagicMock) as lock_mock,\
             mock.patch('matrix_runner.command.sleep', new_callable=MagicMock) as sleep_mock:

            # ... AND a Command object with a mock'ed function but specific parameters is used
            cmd = Command(MagicMock, exclusive=True, needs_shell=True, timeout=60, rest_period=10)
            # ... AND using mock'ed result
            result_mock = MagicMock()
            # ... AND letting the execution return exit code 1
            popen_mock.return_value = 1

            def trace_execute(*args, **kwargs):
                lock_mock.return_value._execute(*args, **kwargs)
                return DEFAULT

            popen_mock.side_effect = trace_execute
            # ... AND letting the resolver return a modified command line
            resolve_mock.return_value = cmdline_resolved

            # WHEN executing a given command line
            cmd._execute(cmdline, result_mock)

            # THEN the result is success
            self.assertFalse(result_mock.success)
            # ... AND the resolver got called once with the original command line
            resolve_mock.assert_called_once_with(cmdline)
            # ... AND the executor got called once with the resolved command line and default parameters
            popen_mock.assert_called_once_with(cmdline_resolved, result_mock, needs_shell=True, encoding='utf-8',
                                               timeout=60, extra=ANY)
            # ... AND a FileLock has been created and acquired before executing and released afterwards
            lock_mock.assert_has_calls([call(ANY), call().acquire(poll_intervall=ANY),
                                        call()._execute(cmdline_resolved, result_mock, needs_shell=True,
                                                        encoding='utf-8', timeout=60, extra=ANY), call().release()])
            # ... AND a sleep has been issued
            sleep_mock.assert_called_once_with(10)

    def test_execute_with_report(self):
        cmdline = ['cmd', 'line', 'args']
        cmdline_resolved = ['resolved_cmd', 'line', 'args']

        # GIVEN internal Command functions mock'ed
        with mock.patch('matrix_runner.command.Command._popen', new_callable=MagicMock) as popen_mock,\
             mock.patch('matrix_runner.command.Command._resolve_cmdline', new_callable=MagicMock) as resolve_mock,\
             mock.patch('matrix_runner.command.FileLock', new_callable=MagicMock),\
             mock.patch('matrix_runner.command.sleep', new_callable=MagicMock):
            # ... AND a mock'ed test report filter
            report_result_mock = MagicMock()
            report_mock = NonCallableMagicMock()
            report_mock.apply = MagicMock(return_value=report_result_mock)
            # ... AND a Command object with the test report assigned
            cmd = Command(MagicMock, test_report=report_mock)
            # ... AND using mock'ed result
            result_mock = MagicMock()
            # ... AND letting the execution return exit code 0
            popen_mock.return_value = 0
            # ... AND letting the resolver return a modified command line
            resolve_mock.return_value = cmdline_resolved

            # WHEN executing a given command line
            cmd._execute(cmdline, result_mock)

            # THEN the report has been applied
            report_mock.apply.assert_called_once_with(result_mock)
            # ... AND the report result has been added to the command result
            self.assertEqual(report_result_mock, result_mock.test_report)

    def test_execute_with_report_lambda(self):
        cmdline = ['cmd', 'line', 'args']
        cmdline_resolved = ['resolved_cmd', 'line', 'args']

        # GIVEN internal Command functions mock'ed
        with mock.patch('matrix_runner.command.Command._popen', new_callable=MagicMock) as popen_mock,\
             mock.patch('matrix_runner.command.Command._resolve_cmdline', new_callable=MagicMock) as resolve_mock,\
             mock.patch('matrix_runner.command.FileLock', new_callable=MagicMock),\
             mock.patch('matrix_runner.command.sleep', new_callable=MagicMock):
            # ... AND a mock'ed test report filter
            report_result_mock = MagicMock()
            report_mock = NonCallableMagicMock()
            report_mock.apply = MagicMock(return_value=report_result_mock)
            report_func_mock = MagicMock(return_value=report_mock)
            # ... AND a Command object with the test report assigned
            cmd = Command(MagicMock,
                          test_report=lambda result: report_func_mock(result))  # pylint: disable=unnecessary-lambda
            # ... AND using mock'ed result
            result_mock = MagicMock()
            # ... AND letting the execution return exit code 0
            popen_mock.return_value = 0
            # ... AND letting the resolver return a modified command line
            resolve_mock.return_value = cmdline_resolved

            # WHEN executing a given command line
            cmd._execute(cmdline, result_mock)

            # THEN the report has been evaluated
            report_func_mock.assert_called_once_with(result_mock)
            # ... AND the report has been applied
            report_mock.apply.assert_called_once_with(result_mock)
            # ... AND the report result has been added to the command result
            self.assertEqual(report_result_mock, result_mock.test_report)

    def test_execute_exception(self):
        cmdline = ['cmd', 'line', 'args']
        cmdline_resolved = ['cmd', 'line', 'args']

        # GIVEN internal Command functions mock'ed
        with mock.patch('matrix_runner.command.Command._popen', new_callable=MagicMock) as popen_mock,\
             mock.patch('matrix_runner.command.Command._resolve_cmdline', new_callable=MagicMock) as resolve_mock,\
             mock.patch('matrix_runner.command.FileLock', new_callable=MagicMock) as lock_mock,\
             mock.patch('matrix_runner.command.sleep', new_callable=MagicMock) as sleep_mock:
            # ... AND a Command object with default parameters is used
            cmd = Command(MagicMock)
            # ... AND using mock'ed result
            result_mock = MagicMock()
            # ... AND letting the execution throw a FileNotFoundError exception
            popen_mock.side_effect = FileNotFoundError()
            # ... AND letting the resolver return a modified command line
            resolve_mock.return_value = cmdline_resolved

            # WHEN executing a given command line
            cmd._execute(cmdline, result_mock)

            # THEN the result is failed
            self.assertFalse(result_mock.success)
            # ... AND the resolver got called once with the original command line
            resolve_mock.assert_called_once_with(cmdline)
            # ... AND the executor got called once with the resolved command line and default parameters
            popen_mock.assert_called_once_with(cmdline_resolved, result_mock, needs_shell=False, encoding='utf-8',
                                               timeout=None, extra=ANY)
            # ... AND no FileLock has been acquired
            lock_mock.assert_not_called()
            # ... AND no sleep has been issued
            sleep_mock.assert_not_called()

    def test_popen(self):
        with captured_output() as (stdout, stderr):
            # GIVEN a properly configured logging
            RunnerApplication._configure_logging(logging.INFO)
            # .. AND an empty Result object
            result = Result()

            if is_windows():
                cmd = ['cmd', '/c', '(echo some log output) && (echo error message >&2) && exit 1']
            else:
                cmd = ['bash', '-c', '(echo "some log output") && (echo "error message" >&2) && exit 1']

            # WHEN running a command with log and error output
            exit_status = Command._popen(cmd, result)

            # THEN the return value is the exit code
            self.assertEqual(exit_status, 1)
            # ... AND the Result object has been updated
            self.assertEqual(result.exit_status, 1)
            # ... AND the output has been captured in the Result object
            self.assertRegex(result.output.getvalue(), "some log output")
            self.assertRegex(result.output.getvalue(), "error message")
            # ... AND the output has been forwarded to stdout/stderr accordingly
            self.assertRegex(stdout.getvalue(), "some log output")
            self.assertRegex(stderr.getvalue(), "error message")

    def test_popen_with_shell(self):
        with captured_output() as (stdout, stderr):
            # GIVEN a properly configured logging
            RunnerApplication._configure_logging(logging.INFO)
            # .. AND an empty Result object
            result = Result()

            if is_windows():
                cmd = ['cmd', '/c', '(echo "some log output") && (echo "error message" >&2) && exit 1']
            else:
                cmd = ['bash', '-c', '(echo "some log output") && (echo "error message" >&2) && exit 1']

            # WHEN running a command with shell, log and error output
            exit_status = Command._popen(cmd, result, needs_shell=True)

            # THEN the return value is the exit code
            self.assertEqual(exit_status, 1)
            # ... AND the Result object has been updated
            self.assertEqual(result.exit_status, 1)
            # ... AND the output has been captured in the Result object
            self.assertRegex(result.output.getvalue(), "some log output")
            self.assertRegex(result.output.getvalue(), "error message")
            # ... AND the output has been forwarded to stdout/stderr accordingly
            self.assertRegex(stdout.getvalue(), "some log output")
            self.assertRegex(stderr.getvalue(), "error message")

    def test_popen_with_timeout(self):
        # GIVEN a properly configured logging
        logging.basicConfig(level=logging.DEBUG)
        # .. AND an os-dependent command line with long running command
        if is_windows():
            cmd = ['powershell', '-Command', 'Wait-Event -SourceIdentifier "Terminate"']
        else:
            cmd = ['bash', '-c', '(bash -c \'while true; do sleep 30; done\') & wait']
        # .. AND an empty Result object
        result = Result()

        # WHEN running a command with shell, log and error output
        with self.assertRaises(TimeoutError):
            Command._popen(cmd, result, timeout=10)

        # THEN the result's exit status contains the TimeoutError
        self.assertIsInstance(result.exit_status, TimeoutError)

    def test_popen_with_whitespace(self):
        # GIVEN a properly configured logging
        logging.basicConfig(level=logging.DEBUG)
        # .. AND a test output message
        message = 'Hello from a script with whitespace.'
        # .. AND an os-dependent script
        if is_windows():
            suffix = '.bat'
            content = dedent(f'''
                @echo off
                echo "{message}"
                echo %*
            ''')
        else:
            suffix = '.sh'
            content = dedent(f'''\
                #!/bin/sh
                echo "{message}"
                echo $*
            ''')
        # .. AND written to a temporary file
        with NamedTemporaryFile(mode='w+t', delete=False,
                                dir=Path.cwd(), prefix='script with whitespace ', suffix=suffix) as script:
            script.write(dedent(content))
            self.addCleanup(os.unlink, script.name)
        # .. AND having the file being executable
        Path(script.name).chmod(0o777)
        # .. AND an empty Result object
        result = Result()

        # WHEN running a command with shell, log and error output
        exit_status = Command._popen([script.name, 'arg1', 'arg2'], result, needs_shell=False)

        # THEN the exit status reflects success
        self.assertEqual(exit_status, 0)
        # ... AND the message has been captured in the Result object
        self.assertRegex(result.output.getvalue(), message)
        # ... AND the arguments have been captured in the Result object
        self.assertRegex(result.output.getvalue(), 'arg1')
        self.assertRegex(result.output.getvalue(), 'arg2')

    def test_popen_shell_with_whitespace(self):
        # GIVEN a properly configured logging
        logging.basicConfig(level=logging.DEBUG)
        # .. AND a test output message
        message = 'Hello from a script with whitespace.'
        # .. AND an os-dependent script
        if is_windows():
            suffix = '.bat'
            content = dedent(f'''
                @echo off
                echo "{message}"
                echo %*
            ''')
        else:
            suffix = '.sh'
            content = dedent(f'''
                #!/bin/sh
                echo "{message}"
                echo $*
            ''')
        # .. AND written to a temporary file
        with NamedTemporaryFile(mode='w+t', delete=False,
                                dir=Path.cwd(), prefix='script with whitespace ', suffix=suffix) as script:
            script.write(dedent(content))
            self.addCleanup(os.unlink, script.name)
        # .. AND having the file being executable
        Path(script.name).chmod(0o777)
        # .. AND an empty Result object
        result = Result()

        # WHEN running a command with shell, log and error output
        exit_status = Command._popen([script.name, 'arg1', 'arg2'], result, needs_shell=True)

        # THEN the exit status reflects success
        self.assertEqual(exit_status, 0)
        # ... AND the message has been captured in the Result object
        self.assertRegex(result.output.getvalue(), message)
        # ... AND the arguments have been captured in the Result object
        self.assertRegex(result.output.getvalue(), 'arg1')
        self.assertRegex(result.output.getvalue(), 'arg2')
