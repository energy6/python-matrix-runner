# -*- coding: utf-8 -*-

import re
import subprocess

from setuptools import setup


def version_from_git_tag():
    """Retrieve version from git history."""
    # Using package version according to PEP 440 -- Version Identification and Dependency Specification
    # https://www.python.org/dev/peps/pep-0440/#local-version-identifiers
    pattern = "^v((\\d+)\\.(\\d+)\\.(\\d+)((a|b|rc)\\d+)?(\\.post\\d+)?(\\.dev\\d+)?)(-(\\d+)-g([0-9a-f]{7}))?$"
    describe = subprocess.check_output(["git", "describe", "--tags", "--match", "v*"]).rstrip().decode()
    match = re.match(pattern, describe)
    if match.group(10) and match.group(11):
        return f"{match.group(1)}+git{match.group(10)}.{match.group(11)}"
    return match.group(1)


setup(
    name='python-matrix-runner',
    version=version_from_git_tag(),
    packages=['matrix_runner'],
    install_requires=open('requirements.txt').read(),
    entry_points={
        'console_scripts': ['matrix-runner-inspect=matrix_runner.inspect:InspectRunner'],
    },
    python_requires='>=3.8',
    url='',
    license='BSD 3-Clause License',
    author='Jonatan Antoni',
    author_email='jonatan@familie-antoni.de',
    description='Helper to run command with matrix configurations',
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst'
)
