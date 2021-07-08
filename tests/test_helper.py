# -*- coding: utf-8 -*-
from enum import Enum
from unittest import TestCase
from unittest.mock import MagicMock

from matrix_runner._helper import fnmatch_ex, partial_with_inspect


class TestHelper(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    def test_fnmatch_ex_str(self):
        self.assertTrue(fnmatch_ex("Cortex-M55NS", "Cortex-M55*"))
        self.assertTrue(fnmatch_ex("Cortex-M55NS", "Cortex-M[235][35]*"))
        self.assertFalse(fnmatch_ex("Cortex-M55NS", "*M55S"))

    def test_fnmatch_ex_tuple(self):
        self.assertTrue(fnmatch_ex(("Cortex-M55NS", "CM55NS"), "Cortex-M55*"))
        self.assertTrue(fnmatch_ex(("Cortex-M55NS", "CM55NS"), "CM55*"))
        self.assertFalse(fnmatch_ex(("Cortex-M55NS", "CM55NS"), "*M55S"))

    def test_fnmatch_ex_enum(self):
        class FnmatchEnum(Enum):
            VALUE1 = "Cortex-M0plus"
            VALUE2 = ("Cortex-M0plus", "Cortex-M0+", "CM0P")

        self.assertTrue(fnmatch_ex(FnmatchEnum.VALUE1, "Cortex-M0*"))
        self.assertTrue(fnmatch_ex(FnmatchEnum.VALUE2, "Cortex-M0*"))
        self.assertTrue(fnmatch_ex(FnmatchEnum.VALUE2, "CM0*"))
        self.assertFalse(fnmatch_ex(FnmatchEnum.VALUE2, "Cortex-M[379]"))

    def test_fnmatch_ex_bool(self):
        self.assertTrue(fnmatch_ex((True, 1), "True"))

    def test_fnmatch_ex_numeric(self):
        self.assertTrue(fnmatch_ex(4711, "47*"))

    def test_partial_with_inspect(self):
        # GIVEN a mock'ed function
        func_mock = MagicMock()

        def func(arg1, arg2, arg4, arg3=None, arg5=None):
            func_mock(arg1, arg2, arg4, arg3=arg3, arg5=arg5)
        # ... AND binding some arguments
        binding = partial_with_inspect(func, "arg1", "arg2", arg3=42)

        # WHEN calling the wrapped function with additional arguments
        binding("arg4", arg5=4711)

        # THEN the mock'ed function has been called with all the arguments
        func_mock.assert_called_once_with("arg1", "arg2", "arg4", arg3=42, arg5=4711)
        # ... AND the name can be retrieved
        self.assertEqual(func.__name__, "func")
        # ... AND the bound arguments can be retrieved
        self.assertEqual("arg1", binding.arg1, "arg1")
        self.assertEqual("arg2", binding.arg2, "arg2")
        self.assertEqual(42, binding.arg3)

    def test_partial_with_inspect_var(self):
        # GIVEN a mock'ed function with variable arguments
        func_mock = MagicMock()

        def func(*args, **kwargs):
            func_mock(*args, **kwargs)
        # ... AND binding some arguments
        binding = partial_with_inspect(func, "arg1", "arg2", arg3=42)

        # WHEN calling the wrapped function with additional arguments
        binding("arg4", arg5=4711)

        # THEN the mock'ed function has been called with all the arguments
        func_mock.assert_called_once_with("arg1", "arg2", "arg4", arg3=42, arg5=4711)
        # ... AND the bound arguments can be retrieved
        self.assertEqual(("arg1", "arg2"), binding.args)
        self.assertEqual({'arg3': 42}, binding.kwargs)

    def test_partial_with_inspect_unbound(self):
        # GIVEN a mock'ed function bound with some arguments
        binding = partial_with_inspect(MagicMock(__name__='func'), "arg1", "arg2", arg3=42)

        # WHEN retrieving an invalid argument
        # THEN an AttributeError is raised
        with self.assertRaises(AttributeError):
            self.assertIsNone(binding.invalid_arg)
