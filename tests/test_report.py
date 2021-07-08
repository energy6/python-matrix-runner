# -*- coding: utf-8 -*-

import os

from io import StringIO
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock

from matrix_runner.report import ConsoleReport, FileReport, CropReport, TransformReport, JUnitReport, ReportFilter


class TestReport(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    def test_file(self):
        # GIVEN some test data writen to a file
        data = '\n.\n'.join(".some..a...c.more.deep.d.content..b...".split('.'))
        with NamedTemporaryFile(mode="wt", delete=False) as file:
            self.addCleanup(os.unlink, file.name)
            file.write(data)

        # WHEN creating a FileReport filter for the file
        chain = FileReport(file.name)
        # ... AND applying the filter chain
        report = chain.apply(MagicMock())
        self.addCleanup(report.stream.close)

        # THEN the report contains the test data
        self.assertEqual(data, report.getvalue())
        # ... AND the data can be read multiple times
        self.assertEqual(data, report.getvalue())

    def test_file_not_found(self):
        # GIVEN  a FileReport filter for a non-existing file
        chain = FileReport("file_not_found")

        # WHEN applying the filter chain
        report = chain.apply(MagicMock())

        # THEN the resulting report contains a RuntimeError
        with self.assertRaises(RuntimeError):
            report.getvalue()

    def test_chain(self):
        # GIVEN a mock'ed command result with some data
        data = StringIO('\n.\n'.join("...a...c...d...b...".split('.')))
        result_mock = MagicMock()
        type(result_mock).output = data

        data2 = StringIO('\n.\n'.join(".some..a...c.more.deep.d.content..b...".split('.')))
        result_mock2 = MagicMock()
        type(result_mock2).output = data2

        # WHEN chaining some report filters
        chain = ConsoleReport() | CropReport('^a$', '^b$') | CropReport('^c$', '^d$')
        # ... AND applying the filter chain to the command result
        report = chain.apply(result_mock)
        report2 = chain.apply(result_mock2)

        # THEN the chain can be walked
        self.assertEqual(CropReport, type(chain))
        self.assertEqual(CropReport, type(chain._other))
        self.assertEqual(ConsoleReport, type(chain._other._other))
        self.assertEqual(None, chain._other._other._other)
        # ... AND the result chain can be walked
        self.assertEqual(CropReport.Result, type(report))
        self.assertEqual(CropReport.Result, type(report._other))
        self.assertEqual(ConsoleReport.Result, type(report._other._other))
        self.assertEqual(None, report._other._other._other)
        # ... AND the final data is the expected filter result
        self.assertEqual('\n.\n'.join("c...d\n".split('.')), report.getvalue())
        self.assertEqual('\n.\n'.join("c.more.deep.d\n".split('.')), report2.getvalue())

    def test_crop(self):
        data = StringIO("""some prolog
which doesn't matter
=== begin ===
this is
relevant data
=== end ===
some epilog
to be ignored
""")
        expected = """=== begin ===
this is
relevant data
=== end ===
"""
        # GIVEN some input data stream
        datasrc = MagicMock()
        type(datasrc).stream = PropertyMock(return_value=data)

        # WHEN applying a crop filter to it
        crop = CropReport('[=]+ begin [=]+', '[=]+ end [=]+')
        report = crop.apply(None)
        report._other = datasrc

        # THEN only the matching section is kept
        self.assertEqual(expected, report.getvalue())

    def test_transform(self):
        dom = StringIO("""
            <xml>
                <element name="test"/>
            </xml>
        """)
        xslt = StringIO("""
            <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
                <xsl:output method="xml" indent="yes"/>
                <xsl:template match="/">
                    <newxml>
                        <xsl:variable name="name" select="//xml/element/@name"/>
                        <newelement data="{$name}"/>
                    </newxml>                
                </xsl:template>
            </xsl:stylesheet>
        """)

        # GIVEN some XML input data stream
        datasrc = MagicMock()
        type(datasrc).stream = PropertyMock(return_value=dom)

        # WHEN applying a transform filter to it
        transform = TransformReport(xslt)
        report = transform.apply(None)
        report._other = datasrc

        # THEN the XML data is transformed
        self.assertEqual("""<newxml>\n  <newelement data="test"/>\n</newxml>\n""", report.getvalue())

    def test_transform_with_schema_error(self):
        dom = StringIO("""
            <xml>
                <element name="test">
        """)
        xslt = StringIO("""
            <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
                <xsl:output method="xml" indent="yes"/>
                <xsl:template match="/">
                    <newxml>
                        <xsl:variable name="name" select="//xml/element/@name"/>
                        <newelement data="{$name}"/>
                    </newxml>                
                </xsl:template>
            </xsl:stylesheet>
        """)

        # GIVEN some XML input data stream with schema errors
        datasrc = MagicMock()
        type(datasrc).stream = PropertyMock(return_value=dom)

        # WHEN applying a transform filter to it
        transform = TransformReport(xslt)
        report = transform.apply(None)
        report._other = datasrc

        # THEN a RuntimeError is raised
        with self.assertRaises(RuntimeError):
            report.getvalue()

    def test_junit(self):
        junit = StringIO("""
            <testsuites>
                <testsuite name="test suite" tests="8" time="0" failures="1" errors="0" skipped="2">
                    <testcase name="test1"/>
                    <testcase name="test2">
                        <skipped/>
                    </testcase>
                    <testcase name="test3">
                        <skipped/>
                    </testcase>
                    <testcase name="test4"/>
                    <testcase name="test5">
                        <failure>
                            Assertion failed in testcase5.c:12!
                        </failure>
                    </testcase>
                    <testcase name="test6"/>
                    <testcase name="test7"/>
                    <testcase name="test8"/>
                </testsuite>
            </testsuites>
        """)

        # GIVEN some JUnit XML input data stream
        datasrc = MagicMock()
        type(datasrc).stream = PropertyMock(return_value=junit)

        # WHEN applying a JUnit filter to it
        junitfilter = JUnitReport()
        report = junitfilter.apply(None)
        report._other = datasrc

        # THEN the summary returns the values from the input data
        self.assertEqual((5, 6), report.summary)

    def test_junit_with_schema_error(self):
        junit = StringIO("""
            <testsuites>
                <testsuite name="test suite" tests="8" time="0" failures="1" errors="0" skipped="2">
                    <testcase name="test1"/>
                    <testcase name="test2">
        """)

        # GIVEN some broken JUnit XML input data stream
        datasrc = MagicMock()
        type(datasrc).stream = PropertyMock(return_value=junit)

        # WHEN applying a JUnit filter to it
        junitfilter = JUnitReport()
        report = junitfilter.apply(None)
        report._other = datasrc

        # THEN a RuntimeError is raised
        with self.assertRaises(RuntimeError):
            self.assertIsNone(report.summary)


class TestReportFilter(TestCase):
    # pylint: disable=protected-access
    # pylint: disable=missing-function-docstring
    # pylint: disable=missing-class-docstring

    def test_cached_value(self):
        # GIVEN a function decorated with cached
        @ReportFilter.Result.cached("_cached_value")
        def func(obj):
            return obj()
        # ... AND a mock object with an empty cache attribute returning a well known value
        value = MagicMock()
        obj_mock = MagicMock(return_value=value)
        type(obj_mock)._cached_value = None

        # WHEN calling the function twice
        return_value1 = func(obj_mock)
        return_value2 = func(obj_mock)

        # THEN both times the well known value is returned
        self.assertEqual(value, return_value1)
        self.assertEqual(value, return_value2)
        # ... AND the actual function is only called once
        obj_mock.assert_called_once()
        # ... AND the cache attribute is updated
        self.assertEqual(value, obj_mock._cached_value)

    def test_cached_except(self):
        # GIVEN a function decorated with cached
        @ReportFilter.Result.cached("_cached_value")
        def func(obj):
            return obj()
        # ... AND a mock object with an empty cache attribute raising a RuntimeError
        obj_mock = MagicMock(side_effect=RuntimeError)
        type(obj_mock)._cached_value = None

        # WHEN calling the function twice
        with self.assertRaises(RuntimeError):
            func(obj_mock)
        with self.assertRaises(RuntimeError):
            func(obj_mock)

        # THEN the actual function is only called once
        obj_mock.assert_called_once()
        # ... AND the cache attribute is updated
        self.assertIsInstance(obj_mock._cached_value, RuntimeError)
