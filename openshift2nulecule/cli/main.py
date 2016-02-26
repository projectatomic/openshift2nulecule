# -*- coding: utf-8 -*-

import os

import argparse
import logging
import anymarkup

from openshift2nulecule.openshift import OpenshiftClient
from openshift2nulecule import utils

logger = logging.getLogger()
logger.handlers = []
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()

logfile_formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
stdout_formatter = '%(levelname)s - %(message)s'
formatter = logging.Formatter(stdout_formatter)
ch.setFormatter(formatter)
logger.addHandler(ch)


class CLI():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--output",
                                 help="Directory where new Nulecule app"
                                 " will be created (must not exist)",
                                 type=str,
                                 required=True)
        self.parser.add_argument("--project",
                                 help="OpenShift project (namespace) to export"
                                      " as Nulecule application",
                                 type=str,
                                 required=True)
        self.parser.add_argument("--oc",
                                 help="Path to oc binary",
                                 type=str,
                                 required=False)
        self.parser.add_argument("--oc-config",
                                 help="Path to config file for oc command",
                                 type=str,
                                 required=False)
        self.parser.add_argument("--debug",
                                 help="Show debug messages",
                                 action='store_true')

    def run(self):
        args = self.parser.parse_args()

        if args.debug:
            logger.setLevel(logging.DEBUG)

        if utils.in_container() and not os.path.isabs(args.output):
            msg = "If running inside container --output path has to be absolute"
            logger.critical(msg)
            raise Exception(msg)

        nulecule_dir = utils.get_path(args.output)

        if os.path.exists(nulecule_dir):
            msg = "{} must not exist".format(nulecule_dir)
            logger.critical(msg)
            raise Exception(msg)

        artifacts_dir = os.path.join(nulecule_dir, "artifacts", "kubernetes")
        nulecule_file = os.path.join(nulecule_dir, "Nulecule")

        oc = OpenshiftClient(oc=args.oc,
                             namespace=args.project,
                             oc_config=args.oc_config)
        artifacts = oc.export_all()

        # remove  ugly thing to do :-(
        # I don't know hot to get securityContext and Selinux
        # to work on k8s for now :-(
        artifacts = oc.remove_securityContext(artifacts)

        # list of artifact for Nulecule file
        nulecule_artifacts = []

        os.makedirs(artifacts_dir)

        filepath = os.path.join(artifacts_dir, "artifacts.json")
        nulecule_artifacts.append("file://{}".format(os.path.relpath(
            filepath, nulecule_dir)))
        anymarkup.serialize_file(artifacts, filepath, format="json")

        nulecule = {"specversion": "0.0.2",
                    "id": args.project,
                    "metadata": {"name": args.project},
                    "graph": [{"name": args.project,
                               "artifacts":
                               {"kubernetes": nulecule_artifacts}}]}
        anymarkup.serialize_file(nulecule, nulecule_file, format="yaml")

        logger.info("Nulecule application created in {}".format(
            utils.remove_path(nulecule_dir)))


def main():
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
