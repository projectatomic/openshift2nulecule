# -*- coding: utf-8 -*-

import logging
from subprocess import Popen, PIPE
import anymarkup
import ipaddress
import os
import docker

from openshift2nulecule import utils

logger = logging.getLogger(__name__)


class OpenshiftClient(object):

    # path to oc binary
    oc = None
    namespace = None
    oc_config = None

    def __init__(self, oc=None, namespace=None, oc_config=None):
        if oc:
            self.oc = oc
        else:
            self.oc = self._find_oc()

        self.namespace = namespace

        if oc_config:
            self.oc_config = utils.get_path(oc_config)
        else:
            oc_config = None

    def _find_oc(self):
        """
        Determine the path to oc command
        Search /usr/bin:/usr/local/bin

        Returns:
            str: path to oc binary
        """

        test_paths = ['/usr/bin/oc', '/usr/local/bin/oc']

        for path in test_paths:
            test_path = utils.get_path(path)
            logger.debug("trying oc at " + test_path)
            oc = test_path
            if os.access(oc, os.X_OK):
                logger.debug("found oc at " + test_path)
                return oc
        logger.fatal("No oc found in {}. Please provide corrent path to co "
                     "binary using --oc argument".format(":".join(test_paths)))
        return None

    def _call_oc(self, args):
        """
        Runs a oc command with its arguments and returns the results.

        Args:
            args (list): arguments for oc command

        Returns:
            ec:     The exit code from the command
            stdout: stdout from the command
            stderr: stderr from the command
        """

        cmd = [self.oc]
        if self.oc_config:
            cmd.extend(["--config", self.oc_config])
        if self.namespace:
            cmd.extend(["--namespace", self.namespace])

        cmd.extend(args)

        ec, stdout, stderr = self._run_cmd(cmd)

        return (ec, stdout, stderr)

    def export_project(self):
        """
        only kubernetes things for now
        """
        # Resources to export.
        # Don't export Pods for now.
        # Exporting ReplicationControllers should be enough.
        # Ideally this should detect Pods that are not created by
        # ReplicationController and only export those.
        resources = ["replicationcontrollers", "persistentvolumeclaims",
                     "services"]

        # output of this export is kind List
        args = ["export", ",".join(resources), "-o", "json"]
        ec, stdout, stderr = self._call_oc(args)
        objects = anymarkup.parse(stdout, format="json", force_types=None)

        ep = ExportedProject(artifacts=objects)
        return ep

    def _run_cmd(self, cmd, checkexitcode=True, stdin=None):
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


class ExportedProject(object):
    artifacts = None

    def __init__(self, artifacts):
        self.artifacts = artifacts

        # remove  ugly thing to do :-(
        # I don't know hot to get securityContext and Selinux
        # to work on k8s for now :-(
        self._remove_securityContext()

    def _remove_securityContext(self):
        """
        Remove securityContext from all objects in kind_list.
        """

        for obj in self.artifacts['items']:
            #   remove securityContext from pods
            if obj['kind'].lower() == 'pod':
                if "securityContext" in obj['spec'].keys():
                    del obj['spec']["securityContext"]
                for c in obj['spec']["containers"]:
                    if "securityContext" in c.keys():
                        del c["securityContext"]

    def pull_images(self, images, registry, login):
        logger.debug("Pulling images to local registry images: {}, "
                     " registry:{}, login:{}".format(images, registry, login))
        
        # get all images of all ReplicationControllers
        images = []
        for artifact in self.artifacts["items"]:
            if artifact["kind"] == "ReplicationController":
                images.extend(self._get_image_info(artifact, registry))

        docker_client = docker.Client(base_url='unix://var/run/docker.sock')
        login_response = docker_client.login(username=login.split(":")[0],
                                             password=login.split(":")[1],
                                             registry=registry)
        logger.info(login_response)
        for imageinfo in images:
            if imageinfo["private"]:
                image = imageinfo["exposed_image"]
            else:
                image = imageinfo["image"]
            logger.info("Pulling image {}".format(image))
            for line in docker_client.pull(image, stream=True):
                # skip lines with progress bar
                if "progress" not in line:
                    logger.info(line)


    def _get_image_info(self, obj, exposed_registry):
        """
        Checks if image specified in ReplicationController is from internal
        registry. If it is from private registry....
        of registry
        TODO: support for Pod

        Args:
           obj (dict): ReplicationController
           exposed_registry (str): host for exposed OpenShift registry.

        Returns:
            list: of dicts example:
                    [{"kind":"ReplicationController",
                      "name": "foo-bar",
                      "image":"172.17.42.145:5000/foo/bar",
                      "private": "True",
                      "exposed_registry": "example.com/foo/bar}]
        """

        results = []

        for container in obj["spec"]["template"]["spec"]["containers"]:
            # get registry name from image
            registry = container["image"].split("/")[0]
            # get host/ip of registry (remove port)
            host = registry.split(":")[0]

            info = {"kind": obj["kind"],
                    "name": obj["metadata"]["name"],
                    "image": container["image"],
                    "private": None}
            try:
                ip = ipaddress.ip_address(host)
                info["private"] = ip.is_private
                info["exposed_image"] = info["image"].replace(registry, exposed_registry)
            except ValueError:
                # host is not an ip address
                info["private"] = False

            results.append(info)
        return results

