#!/usr/bin/env python

from setuptools import setup, find_packages
from pip.req import parse_requirements

requirements = [str(x.req) for x in parse_requirements("requirements.txt", session=False)]

setup(
    name='gapi4term',
    version='0.8.3',
    description='Command Line for Google Services',
    author='Srivatsan Iyer',
    author_email='supersaiyanmode.rox@gmail.com',
    url='https://github.com/supersaiyanmode/gapi',
    install_requires=requirements,
    packages=find_packages(),
    license="https://opensource.org/licenses/MIT",
    entry_points={
        'console_scripts': [
            'gapi = GApi4Term.gapi:main',
        ],
    }
)
