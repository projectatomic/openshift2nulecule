# -*- coding: utf-8 -*-
import os
from openshift2nulecule.constants import HOST_DIR


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
        return HOST_DIR + path
    else:
        return path
