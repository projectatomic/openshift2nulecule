# OpenShift2Nulecule

This tool is creating new Nulecule application with Kubernetes
artifacts from OpenShift project.


## Limitations
 - Exports only ReplicationControllers, PersistentVolumeClaims, Services.
 - Everything is exported as single artifacts containing everything.
 - If you have images in internal OpenShift Docker registry,
you have to manually export them to accessible registry and update artifact.
 - You probably still need go through artifact and change hostnames and ip address.


# External dependencies
OpenShift client (`oc`) has to be installed and configured to 
connect to OpenShift server.

You can provide path to `oc` binary using `--oc` argument.
If you need pass `--config` option to `oc` binary, you can do that using `--oc-config` argument.

# Installation
RPMs: https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/

You can also run `openshift2nulecule` as Docker container. See "Usege example" for more.


## CentOS7/RHEL7 (ADB/CDK)

### CentOS7 (ADB)
```sh
# enable epel
yum install epel-release

# add tkral/openshift2nulecle copr repository
curl  https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/repo/epel-7/tkral-openshift2nulecle-epel-7.repo > /etc/yum.repos.d/tkral-openshift2nulecle-epel-7.repo

# install openshift2nulecule
yum install openshift2nulecule
```

### RHEL7 (CDK)
```
# enable optional repositories
subscription-manager repos --enable rhel-7-server-optional-rpms 

# enable extras repositories
subscription-manager repos --enable rhel-7-server-extras-rpms

# add EPEL repositories
https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

# add tkral/openshift2nulecle copr repository
curl  https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/repo/epel-7/tkral-openshift2nulecle-epel-7.repo > /etc/yum.repos.d/tkral-openshift2nulecle-epel-7.repo

# install openshift2nulecule
yum install openshift2nulecule
```


# Usage example
Before running this you have to be authenticated to OpenShift with `oc` command.

```sh
openshift2nulecule --output=/path/to/new/myapp --project=myproject
```
This will export whole project `myproject` from OpenShift 
and create new Nulecule application in `/path/to/new/myapp` directory.

## Running as Docker container
Easies way how to run openshift2nulecule as Docker container is to use [Atomic](https://github.com/projectatomic/atomic) tool.

```sh
atomic run tomaskral/openshit2nulecule \
  --project testing \
  --output $HOME/mytest \
  --oc-config=$HOME/.kube/config
```
When you are running openshift2nulecule from container, you have to always specify path to `oc` configuration file (`--oc-config`)
in most cases setting it to default `$HOME/.kube/config` should be enough.

Example of running openshift2nulecule container without Atomic tool:
```sh
docker run -it --rm --privileged --net=host -v /:/host tomaskral/openshit2nulecule \
  --project testing \
  --output $HOME/mytest \
  --oc-config=$HOME/.kube/config

```




# Notes

## Brain Dump
### Required steps
 - Export all artifacts from OpenShift (only k8s compatible)
    - (a) Push images that are in internal OpenShift registry to other registry that will be accessible
        - authenticating to registry
        - pushing images to other registy
    - (b) Expose OpenShift registry [1] and use that
        - exporting registry [1]
        - detection if registry is exposed (images in ReplicationControllers and Pods are using iternal address)
        - authenticating to registry
 - Create Nulecule file

### Links
 - [1]  Exposing the Registry - https://docs.openshift.org/latest/install_config/install/docker_registry.html#exposing-the-registry

