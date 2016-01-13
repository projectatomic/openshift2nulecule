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
        self.parser.add_argument("--url",
                                 help="OpenShift server",
                                 type=str,
                                 required=True)
        self.parser.add_argument("--token",
                                 help="Token for OpenShift",
                                 type=str,
                                 required=True)
 
        self.parser.add_argument("--project",
                                 help="OpenShift project name",
                                 type=str,
                                 required=True)
        self.parser.add_argument("--output",
                                 help="Directory where new Nulecule app"
                                      " will be created (must not exist)",
                                 type=str,
                                 required=True)

    def run(self):
        args = self.parser.parse_args()

        nulecule_dir = os.path.abspath(args.output)

        if os.path.exists(nulecule_dir):
            raise Exception("{} must not exist".format(nulecule_dir))

                
        artifacts_dir = os.path.join(nulecule_dir, "artifacts", "kubernetes")
        nulecule_file = os.path.join(nulecule_dir, "Nulecule")

        print("artifacts_dir = {}".format(artifacts_dir))
     
        oc = OpenshiftClient(args.url, args.token, args.project)
        artifacts = oc.export_all()
        
        os.makedirs(artifacts_dir)

        # list of artifact for Nulecule
        nulecule_artifacts = []
        
        for k in artifacts.keys():
            filename = "{}.json".format(k)
            filepath = os.path.join(artifacts_dir, filename)
            print("Saving {}".format(filepath))
            nulecule_artifacts.append("file://{}".format(
                os.path.relpath(filepath, nulecule_dir)))
            anymarkup.serialize_file(artifacts[k], filepath, format="json")


        nulecule = {"specversion": "0.0.2",
                    "id": args.project,
                    "metadata": {"name": args.project},
                    "graph": [{"name": args.project,
                               "artifacts": {"kubernetes": nulecule_artifacts}}]
                    }
        a = anymarkup.serialize_file(nulecule, nulecule_file, format="yaml")

if __name__ == "__main__":
    cli = CLI()
    cli.run()

