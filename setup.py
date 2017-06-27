import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md')).read()
except IOError:
    README = ''

setup(
    name='GitflowDennis',
    version='0.16.0',
    description='Dennis the release helper',
    packages=find_packages(),
    long_description=README,
    author='Yannis Panousis',
    author_email='yannis@kalohq.com',
    url='https://github.com/kalohq/dennis',
    license='MIT',
    entry_points={
        'console_scripts': [
            'dennis = dennis.console:main',
        ],
    },
)
