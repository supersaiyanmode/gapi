#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
    name='gapi4term',
    version='0.8',
    description='Command Line for Google Services',
    author='Srivatsan Iyer',
    author_email='supersaiyanmode.rox@gmail.com',
    url='https://github.com/supersaiyan/GAPI4Term',
    #packages=['GApi4Term', 'GApi4Term.core', 'GApi4Term.commands'],
    packages=find_packages(),
    scripts=[
        "GApi4Term/gapi"
    ]
)
