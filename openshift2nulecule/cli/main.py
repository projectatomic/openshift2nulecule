# -*- coding: utf-8 -*-

import os

import argparse
import logging
import anymarkup

from openshift2nulecule.constants import (NULECULE_PROVIDERS,
                                          ATOMICAPP_VERSION)
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
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        self.parser.add_argument("--output",
                                 help="Directory where the new Nulecule app will be created (must not exist)",
                                 type=str,
                                 required=True)
        self.parser.add_argument("--project",
                                 help="OpenShift project (namespace) to export as a Nulecule application",
                                 type=str,
                                 required=True)
        self.parser.add_argument("--oc",
                                 help="Path to the oc binary",
                                 type=str,
                                 required=False)
        self.parser.add_argument("--oc-config",
                                 help="Path to the config file for the oc command",
                                 type=str,
                                 required=False)
        self.parser.add_argument("--debug",
                                 help="Show debug messages",
                                 action='store_true')

        self.parser.add_argument("--oc-registry-host",
                                 help="Hostname of the exposed internal OpenShift registry",
                                 required=False)

        self.parser.add_argument("--export-images",
                                 help="Pull images that are specified in OpenShift "
                                      "artifacts to a local Docker instance \n"
                                      "and push them to a remote registry (specified by --registry-host).\n"
                                      "Choices are:\n"
                                      " 'internal': export only images from the internal OpenShift registry\n"
                                      " 'all': export all images even from an external registries\n"
                                      " 'none': do not export any images (default)",
                                 choices=["none", "internal", "all"],
                                 default="none",
                                 required=False)

        self.parser.add_argument("--registry-host",
                                 help="External registry hostname. Images that are pulled from an internal\n"
                                      "OpenShift registry or other registries are pushed there.\n",
                                 required=False)
        self.parser.add_argument("--registry-login",
                                 help="Login information for the external registry (if required) "
                                      "(username:passoword)",
                                 required=False)
        self.parser.add_argument("--skip-push",
                                 help="Don't push images to external registry. (usefull for testing)",
                                 action='store_true')


        self.parser.add_argument("--atomicapp-ver",
                                 help="Specify custom Atomic App version for the Dockerfile that will be generated.",
                                 type=str,
                                 default=ATOMICAPP_VERSION,
                                 required=False)

    def run(self):
        args = self.parser.parse_args()

        if args.debug:
            logger.setLevel(logging.DEBUG)
        logger.debug("Running with arguments {}".format(args))

        if utils.in_container() and not os.path.isabs(args.output):
            msg = "If running inside container --output path has to be absolute path"
            logger.critical(msg)
            raise Exception(msg)

        if not args.skip_push and args.export_images != 'none' and not args.registry_host:
            msg = "With --export-images you also need set --registry-host. If you don't want to push images to registry, you have to use --skip-push"
            logger.critical(msg)
            raise Exception(msg)

        # validate and parse --registry-login
        if args.registry_login is None:
            registry_user = None
            registry_password = None
        elif len(args.registry_login.split(":")) == 2:
            registry_user = args.registry_login.split(":")[0]
            registry_password = args.registry_login.split(":")[1]
        else:
            msg = "Invalid format of --registry-login. Use (username:password)"
            logger.critical(msg)
            raise Exception(msg)

        nulecule_dir = utils.get_path(args.output)

        if os.path.exists(nulecule_dir):
            msg = "{} must not exist".format(nulecule_dir)
            logger.critical(msg)
            raise Exception(msg)

        artifacts_dir = os.path.join(nulecule_dir, "artifacts")
        provider_paths = {provider: os.path.join(artifacts_dir, provider)
                          for provider in NULECULE_PROVIDERS}
        nulecule_file = os.path.join(nulecule_dir, "Nulecule")

        oc = OpenshiftClient(oc=args.oc,
                             namespace=args.project,
                             oc_config=args.oc_config)

        # export project info from openshift
        exported_project = oc.export_project()

        # export images
        if args.export_images != "none":
            if args.export_images == "internal":
                only_internal = True
            elif args.export_images == "all":
                only_internal = False

            exported_project.pull_images(args.oc_registry_host,
                                         oc.get_username(),
                                         oc.get_token(),
                                         only_internal)

            # if registy-host is not set or skip-push is set do not perform push
            if args.registry_host and not args.skip_push:
                exported_project.push_images(args.registry_host,
                                             registry_user,
                                             registry_password,
                                             only_internal)

            exported_project.update_artifacts_images()

        provider_artifacts = {}
        for provider, path in provider_paths.items():
            # list of artifact for Nulecule file
            nulecule_artifacts = []

            os.makedirs(path)
            # create artifact files
            for artifact in exported_project.artifacts[provider]:
                if "name" in artifact["metadata"]:
                    name = artifact["metadata"]["name"]
                else:
                    name = "unknown"
                kind = artifact["kind"]
                filename = "{}-{}.json".format(name, kind)
                filepath = os.path.join(path, filename)

                if os.path.exists(filepath):
                    filepath = utils.get_new_name(filepath)

                nulecule_artifacts.append("file://{}".format(os.path.relpath(
                                          filepath, nulecule_dir)))
                anymarkup.serialize_file(artifact, filepath, format="json")

            provider_artifacts[provider] = nulecule_artifacts

        nulecule = {"specversion": "0.0.2",
                    "id": args.project,
                    "metadata": {"name": args.project},
                    "graph": [{"name": args.project,
                               "artifacts": provider_artifacts}]}
        anymarkup.serialize_file(nulecule, nulecule_file, format="yaml")

        utils.generate_dockerfile(nulecule_dir, args.atomicapp_ver)
        logger.info("Nulecule application created in {}".format(
            utils.remove_path(nulecule_dir)))


def main():
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
