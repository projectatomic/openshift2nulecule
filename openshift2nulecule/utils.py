# -*- coding: utf-8 -*-
import os
from openshift2nulecule.constants import (HOST_DIR, 
                                          NULECULE_SPECVERSION,
                                          NULECULE_PROVIDERS,
                                          ATOMICAPP_VERSION)
import ipaddress

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
