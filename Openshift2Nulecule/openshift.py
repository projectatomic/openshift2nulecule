import logging
from subprocess import Popen, PIPE
import anymarkup
from copy import deepcopy

logger = logging.getLogger(__name__)


class OpenshiftClient(object):

    def export_all(self):
        """
        only kubernetes things for now
        """
        # resources to export
        resources = ["pods",
                     "replicationcontrollers",
                     "persistentvolumeclaims",
                     "services"]
       
        # output of this export is kind List
        cmd = ["oc", "export", ",".join(resources), "-o", "json"]
        ec, stdout, stderr = self._run_cmd(cmd)
        return anymarkup.parse(stdout, format="json", force_types=None)


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
        ":Args:
            checkexitcode: Raise exception on bad exit code
            stdin: input string to pass to stdin of the command
        Returns:
            ec:     The exit code from the command
            stdout: stdout from the command
            stderr: stderr from the command
        """
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate(stdin)
        ec = p.returncode
        logger.debug("\n<<< stdout >>>\n%s<<< end >>>\n", stdout)
        logger.debug("\n<<< stderr >>>\n%s<<< end >>>\n", stderr)

        # If the exit code is an error then raise exception unless
        # we were asked not to.
        if checkexitcode:
            if ec != 0:
                printErrorStatus("cmd failed: %s" % str(cmd))  # For cockpit
                raise AtomicAppUtilsException(
                    "cmd: %s failed: \n%s" % (str(cmd), stderr))

        return ec, stdout, stderr

