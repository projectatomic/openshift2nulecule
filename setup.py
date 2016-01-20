#!/usr/bin/env python

from setuptools import setup, find_packages
import re

def _get_requirements(path):
    try:
        with open(path) as f:
            packages = f.read().splitlines()
    except (IOError, OSError) as ex:
        raise RuntimeError("Can't open file with requirements: %s", repr(ex))
    packages = (p.strip() for p in packages if not re.match("^\s*#", p))
    packages = list(filter(None, packages))
    return packages


def _install_requirements():
    requirements = _get_requirements('requirements.txt')
    return requirements


setup(
    name='openshift2nulecule',
    version='0.0.1',
    description='A tool to create Nulecule from OpenShift',
    author='Tomas Kral',
    author_email='tkral@redhat.com',
    url='https://github.com/kadel/Openshift2Nulecule',
    license="LGPL3",
    entry_points={
        'console_scripts': ['openshift2nulecule=Openshift2Nulecule.cli.main:main'],
    },

    packages=find_packages(),
    include_package_data=True,
    install_requires=_install_requirements()
)




