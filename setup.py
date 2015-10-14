import os
import re

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md')).read()
except IOError:
    README = ''


def get_version():
    version_regex = r"^__version__ = ['\"]([^'\"]*)['\"]"
    with open(os.path.join('dennis', '__init__.py'), 'rt') as f:
        matches = re.search(version_regex, f.read(), re.M)
        if matches:
            return matches.group(1)
        else:
            return RuntimeError('Cannot find version string in dennis package')

setup(
    name='dennis',
    version=get_version(),
    description='Dennis the release helper',
    packages=['dennis'],
    long_description=README,
    author='Yannis Panousis',
    author_email='yannis@lystable.com',
    url='https://github.com/lystable/dennis',
    license='MIT',
    install_requires=[
        'uritemplate'
        'GitPython',
        'git+git://github.com/PyGithub/PyGithub.git@v2.0.0-alpha.4'
    ],
    entry_points={
        'console_scripts': [
            'dennis = dennis.console:main',
        ],
    },
)
