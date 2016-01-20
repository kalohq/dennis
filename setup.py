import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md')).read()
except IOError:
    README = ''


def get_version():
    with open('VERSION', 'r') as f:
        return f.read().strip(' \n\rv')

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
        'uritemplate.py',
        'GitPython',
        'PyGithub',
        'sawyer',
        'jinja2',
        'coloredlogs'
    ],
    dependency_links=[
        'https://github.com/lystable/PyGithub/archive/ca6d43eb3b6ee14637940988fd4ac7eb3c207c79.zip#egg=PyGithub',
        'https://github.com/lystable/sawyer/archive/develop.zip#egg=sawyer'
    ],
    entry_points={
        'console_scripts': [
            'dennis = dennis.console:main',
        ],
    },
)
