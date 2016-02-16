# -*- coding: utf-8 -*-

import logging
from subprocess import Popen, PIPE
import anymarkup
from copy import deepcopy
import ipaddress

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
            self.oc = "oc"

        self.namespace = namespace
        self.oc_config = oc_config

    def get_image_info(self, obj):
        """
        checks if image specified in ReplicationController is from internal
        registry
        TODO: support for Pod

        Args:
           obj (dict): ReplicationController

        Returns:
            list: of dicts example:
                    [{"kind":"ReplicationController",
                      "name": "foo-bar",
                      "image":"172.17.42.145:5000/foo/bar",
                      "private": "True"}]
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
            except ValueError:
                # host is not an ip address
                info["private"] = False

            results.append(info)
        return results

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

    def export_all(self):
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

        image_infos = []

        for o in objects["items"]:
            if o["kind"] == "ReplicationController":
                image_infos.extend(self.get_image_info(o))

        for ii in image_infos:
            if ii["private"]:
                logger.warning("{kind} {name} has image that appears to be"
                               "from local OpenShift registry!!".format(**ii))
        return objects

    def remove_securityContext(self, kind_list):
        """
        Remove securityContext from all objects in kind_list.

        Args:
            kind_list (dict): serialized List of openshift objects

        Returns:
            dict: serialized List of object striped from securityContext
        """

        objs = deepcopy(kind_list)
        for obj in objs['items']:
            #   remove securityContext from pods
            if obj['kind'].lower() == 'pod':
                if "securityContext" in obj['spec'].keys():
                    del obj['spec']["securityContext"]
                for c in obj['spec']["containers"]:
                    if "securityContext" in c.keys():
                        del c["securityContext"]
        return objs

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
