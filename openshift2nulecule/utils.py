# -*- coding: utf-8 -*-
import os
from openshift2nulecule.constants import (HOST_DIR, 
                                          NULECULE_SPECVERSION,
                                          NULECULE_PROVIDERS,
                                          ATOMICAPP_VERSION)


def in_container():
    """
    Determine if we are inside container.

    Returns:
        bool: True if inside container
    """

    if os.path.isdir(HOST_DIR):
        return True
    else:
        return False


def remove_path(path):
    """
    Remove /host from path added by get_path
    This is useful for logging

    Args:
        path (str): original path

    Returns:
        str: path without /host prefix
    """
    if in_container():
        if path.startswith(HOST_DIR):
            return path[len(HOST_DIR):]
    return path


def get_path(path):
    """
    Return path prefixed with /host if program is running inside
    container

    Args:
        path (str): original path

    Returns:
        str: path with prefixed /host if inside container
    """
    if in_container():
        return HOST_DIR + os.path.abspath(path)
    else:
        expanded_path = os.path.expanduser(path)
        if os.path.isabs(expanded_path):
            return expanded_path
        else:
            return os.path.abspath(expanded_path)


def generate_dockerfile(nulecule_dir):

    files = [file for file in os.listdir(nulecule_dir)
             if os.path.isfile(os.path.join(nulecule_dir, file))]
    files.append('Dockerfile')
    dockerfile = open(os.path.join(nulecule_dir, 'Dockerfile'), 'w')

    dockerfile.writelines([
        'FROM projectatomic/atomicapp:{}\n'.format(ATOMICAPP_VERSION),
        '\n',
        'LABEL io.projectatomic.nulecule.providers="{}" \\\n'.format(
            ','.join(NULECULE_PROVIDERS)),
        '      io.projectatomic.nulecule.specversion="{}"\n'.format(
            NULECULE_SPECVERSION),
        '\n',
        'ADD {} /application-entity/\n'.format(" ".join(files)),
        'ADD /artifacts /application-entity/artifacts'
    ])
    dockerfile.close()
