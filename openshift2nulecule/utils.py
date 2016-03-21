# -*- coding: utf-8 -*-
import os
from subprocess import Popen, PIPE
import logging
import itertools
from openshift2nulecule.constants import (HOST_DIR,
                                          NULECULE_SPECVERSION,
                                          NULECULE_PROVIDERS)
import ipaddress

logger = logging.getLogger(__name__)


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


def generate_dockerfile(nulecule_dir, atomicapp_version):
    """
    Generate a Dockerfile for an exported application automatically, by
    reading the contents of the directory where the exported artifacts reside.

    Args:
        nulecule_dir (str): path to the directory where all Nulecule artifacts
                            reside
        atomicapp_version (str): Atomic App version to be used in Dockerfile.

    Returns:
        None
    """
    files = [file for file in os.listdir(nulecule_dir)
             if os.path.isfile(os.path.join(nulecule_dir, file))]
    files.append('Dockerfile')
    dockerfile = open(os.path.join(nulecule_dir, 'Dockerfile'), 'w')

    dockerfile.writelines([
        'FROM projectatomic/atomicapp:{}\n'.format(atomicapp_version),
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


def parse_image_name(image):
    """
    Parse Docker image name and split it to 3 parts (name, tag, digest)
    Args:
        image (str): image name to parse
    Returns:
       (image_name, tag, digest): image_name - only name of the image (without
                                               tag or digest)
                                  tag - tag of image (part after last colon),
                                        None if there is no tag in image name
                                  digest - digest of image (part after last @),
                                           None if there is no digest in image
                                           name
    """
    tag = None
    image_digest = None
    if "@" not in image:
        # only if images has not defined digest @sha256:aaaaa...
        tag = image.split(":")[-1]
        image_name = ":".join(image.split(":")[:-1])
    else:
        # image with digest
        image_digest = image.split("@")[-1]
        image_name = image.split("@")[0]

    return image_name, tag, image_digest


def replace_registry_host(image_name, new_registry):
    """
    Replaces registry host in image name

    Args:
        image_name: image name
        new_registry: new registry, that will replace old one in image name

    Return:
        str: new image name with replaced registry part
    """
    return "{}/{}".format(new_registry, "/".join(image_name.split("/")[1:]))


def get_image_info(obj):
    """
    Checks if image specified in ReplicationController is from internal
    registry. If it is from internal registry....
    of registry
    TODO: support for Pod

    Args:
       obj (dict): ReplicationController

    Returns:
        list of dicts example:
                [{"image":"172.17.42.145:5000/foo/bar",
                  "original_image":"172.17.42.145:5000/foo/bar",
                  "internal": "True"}]

                `original_image` shouldn't be ever modified,
                `image` can be modified when pulling and pushing
                images between registries
    """

    results = []

    for container in obj["spec"]["template"]["spec"]["containers"]:
        # get registry name from image
        registry = container["image"].split("/")[0]
        # get host/ip of registry (remove port)
        host = registry.split(":")[0]

        info = {"image": container["image"],
                "original_image": container["image"],
                "internal": None}
        try:
            ip = ipaddress.ip_address(host)
            info["internal"] = ip.is_private
            # TODO: that ip address is private doesn't mean that this
            # is internal OpenShift registry
        except ValueError:
            # host is not an ip address
            info["internal"] = False

        results.append(info)
    return results


def run_cmd(cmd, checkexitcode=True, stdin=None):
    """
    Runs a command with its arguments and returns the results. If
    the command gives a bad exit code then a CalledProcessError
    exceptions is raised, just like if check_call() were called.

    Args:
        checkexitcode: Raise exception on bad exit code
        stdin: input string to pass to stdin of the command

    Returns:
        ec:     The exit code from the command
        stdout: stdout from the command
        stderr: stderr from the command
    """
    logger.debug("running cmd %s", cmd)
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(stdin)
    ec = p.returncode
    logger.debug("\n<<< stdout >>>\n%s<<< end >>>\n", stdout)
    logger.debug("\n<<< stderr >>>\n%s<<< end >>>\n", stderr)

    # If the exit code is an error then raise exception unless
    # we were asked not to.
    if checkexitcode:
        if ec != 0:
            logger.error("cmd failed: %s" % str(cmd))
            raise Exception("cmd: %s failed: \n%s" % (str(cmd), stderr))

    return ec, stdout, stderr


def get_new_name(filepath):
    """
    If filepath exists get new one that doesn't.
    Changes filename of file in path.
    Example:
      if /foo/bar.json exists retruns /foo/bar_1.json

    Args:
      filepath - existing filepath

    Returns:
      str - new filepath that is not existing.

    """
    base, ext = os.path.splitext(filepath)
    new_filepath = filepath
    i = itertools.count(1)
    while os.path.exists(new_filepath):
        #  create new path with index /foo/bar_1.json
        new_filepath = "{}_{}{}".format(base, i.next(), ext)
    return new_filepath
