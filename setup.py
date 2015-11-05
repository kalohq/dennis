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
        'https://github.com/PyGithub/PyGithub/archive/c7a85c0d7b5c0b36d5f48a50008d0e15fb900d8c.zip#egg=PyGithub',
        'https://github.com/lystable/sawyer/archive/develop.zip#egg=sawyer'
    ],
    entry_points={
        'console_scripts': [
            'dennis = dennis.console:main',
        ],
    },
)
