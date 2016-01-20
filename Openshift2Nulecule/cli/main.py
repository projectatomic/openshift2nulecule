# -*- coding: utf-8 -*-
import os
import sys

import argparse
import logging
import anymarkup

from Openshift2Nulecule.openshift import OpenshiftClient


class CLI():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--output",
                                 help="Directory where new Nulecule app"
                                      " will be created (must not exist)",
                                 type=str,
                                 required=True)
        self.parser.add_argument("--app-name",
                                 help="Name of new Nulecule application",
                                 type=str,
                                 required=True)

    def run(self):
        args = self.parser.parse_args()

        nulecule_dir = os.path.abspath(args.output)

        if os.path.exists(nulecule_dir):
            raise Exception("{} must not exist".format(nulecule_dir))
                
        artifacts_dir = os.path.join(nulecule_dir, "artifacts", "kubernetes")
        nulecule_file = os.path.join(nulecule_dir, "Nulecule")

        os.makedirs(artifacts_dir)
     
        oc = OpenshiftClient()
        artifacts = oc.export_all()
        
        # remove  ugly thing to do :-( 
        #I don't know hot to get securityContext and Selinux
        #o work on k8s for now :-(
        artifacts = oc.remove_securityContext(artifacts)
        
        # list of artifact for Nulecule file
        nulecule_artifacts = []
        
        filepath = os.path.join(artifacts_dir, "artifacts.json")
        nulecule_artifacts.append("file://{}".format(os.path.relpath(filepath, nulecule_dir)))
        anymarkup.serialize_file(artifacts, filepath, format="json")

        nulecule = {"specversion": "0.0.2",
                    "id": args.app_name,
                    "metadata": {"name": args.app_name},
                    "graph": [{"name": args.app_name,
                               "artifacts": {"kubernetes": nulecule_artifacts}}]
                    }
        anymarkup.serialize_file(nulecule, nulecule_file, format="yaml")

def main():
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()

