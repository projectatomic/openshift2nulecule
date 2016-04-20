# OpenShift2Nulecule

This tool creates a Nulecule application that has Kubernetes and OpenShift
artifacts based on an existing OpenShift project.

OpenShift2Nulecule creates a nulecule file with artifacts.  Images are
not exported or included in the application.  Images are optionally able
to be exported from the OpenShift registry to another registry.

## Limitations

### Exported Artifacts

OpenShift2Nulecule creates only the following Kubernetes configurations:
  - ReplicationControllers
  - PersistentVolumeClaims
  - Services

OpenShift2Nulecule creates only the following OpenShift configurations:
  - Service
  - DeploymentConfig
  - BuildConfig
  - ImageStream
  - ReplicationController
  - PersistentVolumeClaim

Specifically, OpenShift2Nulecule does not export these OpenShift configurations:
  - Build
  - ImageStreamTag
  - ImageStreamImage
  - Event
  - Node
  - Pod
  - PersistentVolume
 
**You advised to carefully review the created artifacts and change
hostnames and ip addresses.**

For more information about
OpenShift object types, please see the [OpenShift
Documentation](https://docs.openshift.com/enterprise/3.0/cli_reference/basic_cli_operations.html#object-types)
on this topic.

### Kubernetes Usage

OpenShift applications exported for use with Kubernetes by
OpenShift2Nulecule will not be setup to be built from source (s2i).
They will export the last successfully built images from OpenShift to
be launched by Kubernetes.

# External Dependencies

The OpenShift client (`oc`) has to be installed and configured to connect
to OpenShift server.  Additionally, the workstation running
`openshift2nulecule` must have a working copy of the `docker` cli
installed.

You can provide the path to `oc` binary using `--oc` argument. If you
need to pass a `--config` option to the `oc` binary, use the `--oc-config`
option.

# Usage

Before running OpenShift2Nulecule you have to be
authenticated to OpenShift using the `oc login`
command. For more information, see [Basic Setup and
Login](https://docs.openshift.com/enterprise/3.0/cli_reference/get_started_cli.html#basic-setup-and-login).

## Export A Whole Project

```sh
openshift2nulecule --output /path/to/new/myapp --project myproject
```
This will export the whole OpenShift project, `myproject`, and create
a new Nulecule application in the `/path/to/new/myapp` directory.

## Selectively Export an Application Based on Labels

```bash
openshift2nulecule --output ~/exported/hexboard --project hexboard --selector app=sketchpod
```

This will export the just the `sketchpod` application from the OpenShift
project, `myproject`, and create a new Nulecule application in the
`/path/to/new/myapp` directory.


## Exporting Images From OpenShift

This tool has also support for exporting images from the
OpenShift internal registry.  To use this you need to
secure and expose the OpenShift internal registry using
`route`. For instructions please see the [official OpenShift
documentation](https://docs.openshift.org/latest/install_config/install/docker_registry.html#exposing-the-registry).

The following example will export all images that are used in the project
and push them to the registry at `localhost:5000`.

```sh
openshift2nulecule --output ./myapp --project mlb --oc-registry-host docker-registry.cdk.10.2.2.2.xip.io --export-images all --registry-host localhost:5000 
```
For testing you might want to skip push stage. You can do this by adding
`--skip-push` option.  With this option openshift2nulecule will only
pull images to you local docker cache.


## Arguments

General Arguments:
  - `--output` - The path to where the nulecule application should
                 be written.  Can be space or equal separated.
  - `--selector` - A set of `key=value` statements that describe what
                   elements of the OpenShift project should be exported.
  - `--project` - The OpenShift project to operate on. 
  - `--oc` - The path to the `oc` binary.
  - `--oc-config` - Any arguments that should be passed using the `oc`
                    binary's `--config` argument.

The following arguments are related to exporting images:

  - `--export-images` - Which images should be exported from
                        OpenShift. Options are: "all", "internal", "none".
    - *all* - Pulls all images that are specified in artifacts even if
              they are not in the OpenShift internal registry and must
              be downloaded from an external registry.
    - *internal* - Pull only images from the OpenShift internal registry.
    - *none* - No images are pulled. (default)
  - `--oc-registry-host` - Hostname of the exposed OpenShift internal
                           registry.  (Host of the `docker-registry`
                           route.)
  - `--registry-host` - Hostname of registry to push images too.
  - `--registry-login` - The Username and password for authenticating to 
                         the registry which will be pushed too,
                         if required.
  - `--skip-push` - Only pull the images to the local docker cache, do not
                    push them to the new registry.

# Installation

RPMs for use with Fedora, CentOS, and Red Hat Enterprise Linux are
available in COPR at:

`https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/`

Specific Operating System instructions are below

## CentOS 7 and CentOS Atomic Developer Bundle (ADB)

```sh
# enable epel
yum install epel-release

# add tkral/openshift2nulecle copr repository
curl  https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/repo/epel-7/tkral-openshift2nulecle-epel-7.repo > /etc/yum.repos.d/tkral-openshift2nulecle-epel-7.repo

# install openshift2nulecule
yum install openshift2nulecule
```

## Red Hat Enterprise Linux Container Development Kit (CDK)

Installed by default.

### Red Hat Enterprise Linux 7

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

## Running as Docker container

OpenShift2Nulecule can also be run in a Docker container.  It is easier to do when using the [Atomic CLI](https://github.com/projectatomic/atomic).

```sh
atomic run tomaskral/openshift2nulecule \
  --project testing \
  --output $HOME/mytest \
  --oc-config=$HOME/.kube/config \
  --oc-registry-host 172.30.22.38:5000 \
  --export-images all \
  --registry-host my_registry:5000
```

**Note:** When running openshift2nulecule in a container, you must always
specify the path to the `oc` configuration file using the `--oc-config`
argument.  In most cases, the default value of `$HOME/.kube/config`
should work.

Example of running the openshift2nulecule container without the Atomic CLI:

```sh
docker run -it --rm --privileged --net=host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /:/host \
  tomaskral/openshift2nulecule \
  --project testing \
  --output $HOME/mytest \
  --oc-config=$HOME/.kube/config
  --oc-registry-host 172.30.22.38:5000 \
  --export-images all \
  --registry-host my_registry:5000
```
