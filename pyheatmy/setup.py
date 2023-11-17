# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pyheatmy',
    version='0.1.0',
    description='PyHeat',
    long_description=readme,
    author='Mathis Bourdin, Youri Tchouboukoff',
    author_email='mathis.bourdin@mines-paristech.fr, youri.tchouboukoff@mines-paristech.fr',
    url='https://github.com/mathisbrdn/pyheatmy/',
    license=license,
    packages=find_packages(exclude=())
)

