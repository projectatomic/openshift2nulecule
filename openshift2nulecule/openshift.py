# -*- coding: utf-8 -*-

import logging
from subprocess import Popen, PIPE
import anymarkup
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

    @staticmethod
    def _find_oc():
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

    # all images from all artifacts, gets updated with every image operation
    # like pull_images, push_images ...
    images = None

    def __init__(self, artifacts):

        self.artifacts = artifacts

        # remove  ugly thing to do :-(
        # I don't know hot to get securityContext and Selinux
        # to work on k8s for now :-(
        self._remove_securityContext()

        # get all images of all ReplicationControllers
        self.images = []
        for artifact in self.artifacts["items"]:
            # TODO: add support for other kinds (Pod, DeploymentConfig)
            if artifact["kind"] == "ReplicationController":
                self.images.extend(utils.get_image_info(artifact))

    def _remove_securityContext(self):
        """
        Remove securityContext from all objects in kind_list.
        """

        for obj in self.artifacts['items']:
            #  remove securityContext from pods
            if obj['kind'].lower() == 'pod':
                if "securityContext" in obj['spec'].keys():
                    del obj['spec']["securityContext"]
                for c in obj['spec']["containers"]:
                    if "securityContext" in c.keys():
                        del c["securityContext"]

    def pull_images(self, registry, login, only_internal=True):
        """
        This pulls all images that are mentioned in artifact.

        Args:
            registry (str): url of exposed OpenShift Docker registry
            login (str): username:password for OpenShift Docker registry
            only_internal (bool): if True only images that are in internal
                                  OpenShift Docker registry, otherwise pulls
                                  all images (default is True)

        """
        logger.debug("Pulling images to local registry only_internal: {}, "
                     " registry:{}, login:{}".format(only_internal, registry,
                                                     login))

        docker_client = docker.Client(base_url='unix://var/run/docker.sock')
        login_response = docker_client.login(username=login.split(":")[0],
                                             password=login.split(":")[1],
                                             registry=registry)
        logger.info(login_response)
        for image_info in self.images:
            if image_info["internal"]:
                image_info["image"] = utils.replace_registry_host(
                    image_info["image"], registry)
            else:
                if only_internal:
                    # we are exporting only internal images, skip this
                    continue
            image = image_info["image"]
            logger.info("Pulling image {}".format(image))
            for line in docker_client.pull(image, stream=True):
                # skip lines with progress bar
                if "progress" not in line:
                    logger.info(line)
                    # TODO: verify pull success

    def push_images(self, registry, login, only_internal=True):
        """
        This pushes all images that are mentioned in artifact.

        Args:
            registry (str): url of registry
            login (str): username:password for docker registry
            only_internal (bool): if True only images that are in internal
                                  OpenShift Docker registry, otherwise pulls
                                  all images (default is True)

        """
        logger.debug("pushing images to registry only_internal: {}, "
                     " registry:{}, login:{}".format(only_internal, registry,
                                                     login))

        docker_client = docker.Client(base_url='unix://var/run/docker.sock')
        if login:
            login_response = docker_client.login(username=login.split(":")[0],
                                                 password=login.split(":")[1],
                                                 registry=registry)
            logger.debug(login_response)
            # TODO: check login_response
        for image_info in self.images:
            if only_internal and not image_info["internal"]:
                # skip this image
                continue
            image = image_info["image"]

            # new name of image (only replace registry part)
            name_new_registry = utils.replace_registry_host(image, registry)

            (new_name, new_name_tag, new_name_digest) = utils.parse_image_name(
                name_new_registry)

            if new_name_digest:
                # if this is image with define digest, use digest as tag
                # docker cannot push image without tag, and if images
                # is pulled with digest it doesn't have tag specified

                # if this is going to be used as tag, it cannot contain ':'
                tag = new_name_digest.replace(":", "")
            else:
                tag = new_name_tag

            new_full_name = "{}:{}".format(new_name, tag)
            image_info["image"] = new_full_name

            logger.info("tagging image {} as {}".format(image, new_full_name))
            tag_response = docker_client.tag(image, new_name, tag, force=True)
            # TODO: verify tag_response
            logger.debug(tag_response)

            logger.info("pushing image {}".format(new_full_name))
            # TODO: push fails with image with digest
            for line in docker_client.push(new_full_name, stream=True):
                # skip lines with progress bar
                if "progress" not in line:
                    logger.info(line)
                    # TODO: verify if push was success

    def update_artifacts_images(self):
        """
        Update artifact images. When pulling and pushing images
        are renamed (retagged). This updates image names in
        all artifacts.
        """

        for artifact in self.artifacts["items"]:
            # TODO: add support for other kinds (Pod, DeploymentConfig)
            if artifact["kind"] == "ReplicationController":
                for container in \
                        artifact["spec"]["template"]["spec"]["containers"]:
                    for image in self.images:
                        if container["image"] == image["original_image"]:
                            logger.info("Updating image {} for artifact {}:{}"
                                        .format(container["image"],
                                                artifact["kind"],
                                                artifact["metadata"]["name"]))
                            container["image"] = image["image"]
