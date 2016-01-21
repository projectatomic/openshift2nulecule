# OpenShift2Nulecule

This tool is creating new Nulecule application with Kubernetes
artifacts from OpenShift project.


# External dependencies
OpenShift client (`oc`) has to be installed and configured to 
connect to OpenShift server.


# Example
```
openshift2nulecule --output=/path/to/new/myapp --project=myproject
```
This will export whole project `myproject` from OpenShift 
and create new Nulecule application in `/path/to/new/myapp` directory.
