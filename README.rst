Matrix Runner for Python
========================

Allows easy top level command line interface generation for matrix configurations.

Install
-------

Installation using pip::

    pip install python-matrix-runner

The appearance of matrix runner can be configured by placing a copy of the
``default.conf`` into the users Python site base directory (user global
configuration) or next to a build script (local configuration). Figuring out
the right locations is assisted by the following command::

    $ python -m matrix_runner config -h


Preferences
~~~~~~~~~~~

The following preferences can be configured:

global
  Global settings.

  loglevel
    The default log level, one of:
    DEBUG, INFO, WARNING, ERROR, CRITICAL

colors
  Settings for colorized log output.

  Colors can be one of: black, red, green, yellow, blue, purple, cyan, white

  Style prefix can be one of: bold\_, thin\_

  Background color prefix: bg\_

  DEBUG
    Debug level log output.
  INFO
    Info level log output.
  WARNING
    Warning level log output.
  ERROR
    Error level log output.
  CRITICAL
    Critical level log output.
  config
    Matrix configuration column.
  action
    Action column.
  summary_config
    Summary table matrix configuration column.
  summary_success
    Summary table success cell.
  summary_unstable
    Summary table unstable cell, i.e. failing test cases.
  summary_skip
    Summary table skip cell.
  summary_fail
    Summary table fail cell.
  summary_error
    Summary table error cell.

Example Usage
-------------

Writing the following to ``build.py``::

    from enum import Enum
    from matrix_runner import main, matrix_axis, matrix_action, matrix_command, matrix_filter

    @matrix_axis("alpha", "a", "A configuration axis")
    class MyAlphaAxisValue(Enum):
        Value1 = ('value1', 'v1')
        Value2 = ('value2', 'v2')
        Value3 = ('value3', 'v3')

    @matrix_action
    def dump(config):
        """Dump configuration to console"""
        yield dump_config(config)

    @matrix_command()
    def dump_config(config):
        return ["sh", "-c", f"echo '{config}'"]

    if __name__ == "__main__":
        main()

Can be executed as::

    $ ./build.py --help
    usage: build.py [-h] [--silent | --verbose | --debug] [--pairwise]
                    [--alpha ALPHA] action [action ...]

    positional arguments:
      action                Action(s) to run: dump

    optional arguments:
      -h, --help            show this help message and exit
      --silent              Silent mode, only errors are shown.
      --verbose             Verbose log output.
      --debug               Debug log output.
      --pairwise, -2        Reduce number of combinations using pairwise algorithm.
      --alpha ALPHA, -a ALPHA
                            A configuration axis: value1|v1, value2|v2, value3|v3

    $ ./build.py -a v[23] dump
    [value2](dump:dump_config) /usr/bin/sh -c echo 'Config(alpha=<MyAlphaAxisValue.Value2: ('value2', 'v2')>)'
    [value2](dump:dump_config) (Hello, World): Config(alpha=<MyAlphaAxisValue.Value2: (value2, v2)>)
    [value2](dump:dump_config) /usr/bin/sh succeeded with exit code 0
    [value3](dump:dump_config) /usr/bin/sh -c echo 'Config(alpha=<MyAlphaAxisValue.Value3: ('value3', 'v3')>)'
    [value3](dump:dump_config) Config(alpha=<MyAlphaAxisValue.Value3: (value3, v3)>)
    [value3](dump:dump_config) /usr/bin/sh succeeded with exit code 0

    Matrix Summary
    ==============

    alpha    dump
    -------  -------
    value2   success
    value3   success

Matrix Runner automatically generates a comprehensive `command line`_ help.
Giving at least one action the commands for all permutations of configured
matrix axes are automatically executed one by one. In this example the
execution is limited by a regex pattern ``v[23]``.


Detailed Usage
--------------

The Matrix Runner constructs what gets executed by defining these elements:

- Axis_
- Action_
- Command_
- Filter_

Axis
~~~~

Axes build up the actual configuration matrix to be rolled out. Each degree
of freedom in ones set of configuration can be mapped to a single axis by
annotating an ``Enum`` with ``@matrix_axis``::

    @matrix_axis("alpha", abbrev="a", desc="A configuration axis")
    class MyAlphaAxisValue(Enum):
        Value1 = ('value1', 'v1')
        Value2 = ('value2', 'v2')
        Value3 = ('value3', 'v3')

This adds an axis named `alpha` to the current builds configuration matrix.
The optional argument ``abbrev`` can be used to specify a shortcut to be
used from the command line, i.e. ``--alpha`` or ``-a``. And the optional
argument ``desc`` enriches the argument parser with a help string.

The values in such an Enum can either be plain strings or tuples of strings.
Tuples can be used to provide multiple string representations for a single
value. In the example one can provide ``Value2`` on the command line as
``--alpha value2`` or just as ``-a v2``. Alternatively axis values can be
selected by providing a `fnmatch.fnmatch`_ pattern, e.g. ``-a v[23]``. Be aware
that such a pattern selects all values which have at least one matching string
representation in its tuple.

The overall configuration matrix is calculated by permuting all values from all
specified axes. In a typical scenario it easily happens that some combinations
are known to be inappropriate. These can be filtered by specifying Filter_'s.

.. note:: Don't use the keywords ``help`` or ``pairwise`` as axis names. Same
          applies to abbreviations ``h`` and ``2`` for those keywords. These
          are already used for static `Command Line`_ arguments.

Action
~~~~~~

Actions are used to capture different workflow steps, such as `compile` and
`run` for unit tests. A step is simply defined by decorating a function
with ``@matrix_action``::

    @matrix_action
    def dump(config: Config <, results: List[Result]>):
        """Dump configuration to console"""
        pre_process()
        yield dump_config(config, 'Hello', 'World')
        post_process(<results>)

The function itself needs to return a ``Generator`` generating a list of
Command_'s. The function is called once in preparation for each matrix
configuration.

The ``config`` argument gives access to the selected _Config permutation. It
can be used to generate the commands depending on the actual configuration.

The optional ``results`` argument can be used to gain access to the list of
Command_ results gathered so far, e.g. for adding post-processing.

The function needs to ``yield`` Command_'s, i.e. ``dump_config`` needs to be
an annotated command function. Pre and post processing code can be added
around.

Command
~~~~~~~

Commands are actual command lines to be executed while forwarding their
standard output and standard error streams. A command is defined by decorating
a function with ``@matrix_command``::

    @matrix_command()
    def dump_config(*args, **kwargs):
        return ["sh", "-c", f"echo '{args}: {kwargs}'"]

The decorator takes optional keyword arguments to fine control how the returned
command line should be executed through `subprocess.Popen`_:

- ``exit_code: Union[int, Iterable[int], Callable[[int], bool]] = 0``
    Specifies exit codes denoting successful execution of the command, this can
    either be

    - a specific integer exit code, by default ``0``, or
    - a sequence of integer exit codes, e.g. a range, or
    - a function that returns True for successful exit codes.

- ``needs_shell: bool = False``
    Set this to ``True`` if the command requires a shell environment.

- ``encoding: str = 'utf-8'``
    Set this to another character encoding if the command's output does not
    use an UTF-8 compatible character set.

- ``exclusive: bool = False``
    Some command are known to be prone to concurrency issues. Setting this to
    ``True`` will block concurrent invocations of the command, e.g. when using
    Matrix Runner concurrently on the same machine.

- ``timeout: Optional[float] = None``
    Commands prone to hick-ups (i.e. getting stuck) can be automatically killed
    when a specified time span has elapsed [in seconds].

- ``retry: Optional[int] = 1``
    Commands prone to occasional failures can be automatically repeated.
    The result will reflect the latest return code. The output from all
    tries is captured.

- ``rest_period: Optional[float] = None``
    Some commands are known to be prone to concurrency issues. Setting this to
    a value larger than ``0`` adds a rest period (i.e. time.sleep_) before the
    command actually gets executed.

- ``test_report: Optional[ReportFilter] = None``
    By default the result of a command only depends on the ``exit_code``. The
    commands output is captured but not processed by Matrix Runner. By
    specifying a "recipe" how to evaluate results the output can be post
    processed into a detailed Report_.

The actual command function can take arbitrary arguments which can be provided
during the enclosing Action_. All arguments bound to a Command instance can
be inspected by reading the according object attribute, e.g.::

    cmd = dump_config(*args, **kwargs)  # Retrieve the Command object with bound arguments
    print(cmd.args, cmd.kwargs)         # Inspect the Command object's bound arguments

Command Result
^^^^^^^^^^^^^^

For each single invocation of a Command_ the entire output is captured in a
``CommandResult`` object. These objects can be used to inspect the details
of the execution using the following properties:

- ``command: Command``
    A back-reference to the executed Command_ with bound arguments.
- ``cmdline: List``
    The actual command line returned from the command function.
- ``exit_status: Optional[Union[int, TimeoutError]]``
    The exit status returned by the command, or a TimeoutError exception if
    occurred. A ``None`` indicates the command has run to completion, yet.
- ``success: bool``
    Indicator for an overall successful execution. This value is calculated
    from the actual ``exit_status`` and the expected Command_'s ``exit_code``.
- ``output: StringIO``
    The captured ``stdout`` and ``stderr`` from the execution.
- ``test_report: Optional[ReportFilter.Result]``
    The generated `Report Result`_ from applying the Command_'s ``test_report``.
- ``start_time: float``
    The Unix Epoch the command was launched retrieved from ``time.time()``.
- ``end_time: float``
    The Unix Epoch the command was finished ``time.time()``.
- ``start_perf_counter: float``
    The value retrieved from ``time.perf_counter()`` before running the command.
- ``end_perf_counter: float``
    The value retrieved from ``time.perf_counter()`` after running the command.

Report
~~~~~~

A report can capture and post process the output of a command after execution.
This can be used to gather a test report from the commands standard output
into a standardized format. Though, this feature is not limit to test reports.

In order to attach report generation to a Command_ assign a pipe chain of
report generators to ``test_report``. The available report generators are:

- ``ConsoleReport()``
    Captures the console output of the command.
- ``CropReport(first: AnyStr, last: AnyStr)``
    Crops a section out of the input. All lines between first and last
    (inclusive) are kept, everything else is dropped.
- ``TransformReport(xslt)``
    Applies the provided XSLT script to the input.
- ``JUnitReport(title)``
    Treats the input as JUnit XML and provides a detailed summary. Set
    ``title`` to a static string or a function
    ``lambda(title: str <, result: CommandResult]>) -> str``
    to update the test suite names.

Report generators can be chained in pipe like manner::

    ConsoleReport() |
    CropReport("<report>", "</report>") |
    TransformReport("tojunit.xsl") |
    JUnitReport(title = lambda title, report: title)

This chain

- Captures the console output of the command.
- Crops all content between ``<report>`` and ``</report>``, inclusive.
- Transforms the custom XML to JUnit.
- Considers the JUnit results for summary.

The `Report Result`_ is appended to the Command_'s result ``test_report``
property to be accessible, e.g. in Action_ functions.

The report can
be written to a file using its ``write(file: AnyStr)`` function.

Report Result
^^^^^^^^^^^^^

The ``ReportFilter.Result`` gives access to the final output of a Report_
filter chain applied to a specific Command_ result. The following properties
and functions can be used to access the report:

- ``stream -> StringIO``
    Direct access to the text stream.
- ``getvalue() -> str``
    Final string output.
- ``write(file: AnyStr)``
    Write the output into a file.

The mixin ``ReportFilter.Summary`` adds a detailed summary output in addition
to the default ``passed`` or ``failed`` one:

- ``summary -> Tuple[int, int]`` returns a tuple of ``passed`` and ``executed``
    test cases.

Custom Reports
^^^^^^^^^^^^^^

Custom report generators can be added by subclassing ``ReportFilter``
overwriting its inner class ``ReportFilter.Result`` and giving a custom
``stream -> StringIO`` property. The preceding generator can be accessed
through ``_other`` property. In case of an error while processing the report a
RuntimeError should be raised::

    class CustomReport(ReportFilter):
        class Result(ReportFilter.Result):
            @property
            def stream(self) -> StringIO:
                if not self._stream:
                    try:
                        self._stream = StringIO()
                        input = self._other.stream
                        args = self._report.args
                        output = input              # add some modification
                        self._stream.write(output)
                    except SomeException as e:
                        self._stream = e
                if isinstance(self._stream, Exception):
                    raise RuntimeError from self._stream
                else:
                    return self._stream

        def __init__(self, *args):
            super(CustomReport, self).__init__()
            self.args = args

Additional report formats can be supported by mixing in ``ReportFilter.Summary``
and providing a custom ``summary -> Tuple[int, int]`` property. The summary
shall return a tuple with numbers test cases ``(passed, executed)``::

    class CustomSummary(ReportFilter):
        class Result(ReportFilter.Result, ReportFilter.Summary):
            @property
            def summary(self) -> Tuple[int, int]:
                passed = ...   # calculate passed test cases
                executed = ... # calculate executed test cases
                return passed, executed

Filter
~~~~~~

A filter can be used to remove inappropriate Config_'s from the configuration
matrix. This is achieved by defining a function annotated with
``@matrix_filter`` returning ``True`` for configuration to be dropped::

    @matrix_filter
    def filter(config):
        return config.alpha.match('value3')

Config
~~~~~~

A single matrix configuration with specific values for each matrix axis is
denoted by an ``Config`` object. The ``Config`` object contains a property
for each axis containing the value.

In order to check if an axis value matches a condition one can use the
``match`` function providing a `fnmatch.fnmatch`_ pattern.

Command Line
~~~~~~~~~~~~

Running one or more configurations from the command line using Matrix Runner is
trivial. The generated interface looks like this::

    $ ./build.py --help
    usage: build.py [-h] [--silent | --verbose | --debug] [--pairwise]
                    [[--<axis> <AXIS>] ...] action [action ...]

The positional argument ``action`` can be one or multiple define Action_'s to
be executed in the given order, e.g. either ``build`` and ``run`` separately or
both in a sequence.

The optional arguments are a combination of static ones used to parametrize
Matrix Runner itself and dynamic ones generated from the defined Axis_:

- ``-h``, ``--help`` shows the help message
- ``--silent`` Silent mode, only errors are shown.
- ``--verbose`` Verbose log output.
- ``--debug`` Debug log output.
- ``-2``, ``--pairwise`` reduces number of combinations using pairwise algorithm
    This enables combinatorial `all-pairs testing`_ to reduce the overall
    number of configuration in logarithmic manner while retaining a high
    probability of detecting issues.
- ``-<a> <AXIS>``, ``--<axis> <AXIS>`` reduce number of combinations to selected ``AXIS`` values for ``axis``
    Axis values can be given as one of their string representations *or* an
    fnmatch.fnmatch_ pattern matching at least one of these. In case of pattern
    matching *all* matching values are selected. This argument can be given
    multiple time which adds the values in a cumulative way.

The console output has two parts. While executing the actions the output from
the associated commands is forwarded like this::

    [<AXIS>](<ACTION>) <pre processing log>
    [<AXIS>](<ACTION>:<COMMAND>) <command line>
    [<AXIS>](<ACTION>:<COMMAND>) <stdout/stderr from command>
    [<AXIS>](<ACTION>) <post processing log>

Each line of output is prefixed with a ``[<AXIS>]`` per axis giving the
matrix configuration values the output belongs to. Followed by a
``(<ACTION>:<COMMAND>)`` tag denoting the action and command currently
executed. On a color terminal there is a clear distinction between stdout
(green) and stderr (red) output. Intermediate warning messages from Python
are colored as yellow.

After all actions have been executed for all selected configurations a
comprehensive summary is displayed like this::

    Matrix Summary
    ==============

    <axis>   <ACTION>
    -------  -------
    <AXIS>   success
    <AXIS>   FAILED
    <AXIS>   (skip)
    ...      ...

The Matrix Summary gives a table with a column per axis and action. Each line
denotes all actions result for a specific configuration:

- ``success`` (green) denotes all commands have been executed successfully (i.e. with expected exit codes)
- ``FAILED`` (red) denotes a command has returned a failure exit code and execution got stalled
- ``(skip)`` (yellow) denotes that this action has not been performed for that configuration.
    Skipping configuration happens due to Filter_'s.

.. note:: By default Matrix Runner scripts are expected to be run from their
          local directory. Calling a script from anywhere else will create a
          warning and the execution is likely to fail.

.. _subprocess.Popen: https://docs.python.org/3/library/subprocess.html#subprocess.Popen
.. _time.sleep: https://docs.python.org/3/library/time.html?highlight=sleep#time.sleep
.. _fnmatch.fnmatch: https://docs.python.org/3/library/fnmatch.html#fnmatch.fnmatch
.. _all-pairs testing: https://en.wikipedia.org/wiki/All-pairs_testing

Utilities
---------

Inspector
~~~~~~~~~

The command line utility ``matrix-runner-inspect`` can be used to inspect a
Matrix Runner build::

    $ matrix-runner-inspect -h
    usage: matrix-runner-inspect [-h] script

It takes only a single positional argument denoting the script to be inspected,
for example::

    $ matrix-runner-inspect -- example.py
    {
      "axes": {
        "alpha": {"abbrev": "a", "values": ["value1", "value2", "value3"],
                  "desc": "A configuration axis"}
      },
      "matrix": [{"alpha": "value1"}, {"alpha": "value2"}, {"alpha": "value3"}]
    }

The output gives the axes definition and the actual configuration matrix. The
script take all the usual axis arguments as shown above. These can be used to
reduce the matrix reported by inspect::

    $ matrix-runner-inspect -- demo/example.py -a v[23]
    {
      "axes": {"alpha": {"abbrev": "a", "values": ["value1", "value2", "value3"],
               "desc": "A configuration axis"}},
      "matrix": [{"alpha": "value2"}, {"alpha": "value3"}]
    }
