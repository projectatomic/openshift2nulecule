# OpenShift2Nulecule

This tool is creating new Nulecule application with Kubernetes
artifacts from OpenShift project.


## Limitations
 - Exports only `ReplicationControllers`, `PersistentVolumeClaims`, `Services` for *Kubernetes*.
 - Exports only `service`, `deploymentConfig`, `buildConfig`, `imageStream`, `route`, `replicationController`, `persistentVolumeClaim` for *Openshift*, other objects like `build`, `imageStreamTag`, `imageStreamImage`, `event`, `node`, `pod`, `persistentVolume`,  are not exported at the moment.
 - Everything is exported as single artifacts containing everything.
 - ~~If you have images in internal OpenShift Docker registry,
you have to manually export them to accessible registry and update artifact.~~
 - You probably still need go through artifact and change hostnames and ip address.


# External dependencies
OpenShift client (`oc`) has to be installed and configured to 
connect to OpenShift server.

You can provide path to `oc` binary using `--oc` argument.
If you need pass `--config` option to `oc` binary, you can do that using `--oc-config` argument.

# Usage
Before running this you have to be authenticated to OpenShift using `oc login` command. (see [Basic Setup and Login](https://docs.openshift.com/enterprise/3.0/cli_reference/get_started_cli.html#basic-setup-and-login)).

- Export whole project

```sh
openshift2nulecule --output=/path/to/new/myapp --project=myproject
```
This will export whole project `myproject` from OpenShift
and create new Nulecule application in `/path/to/new/myapp` directory.

- Selectively export an application

```bash
openshift2nulecule --project hexboard --output ~/exported/hexboard --selector app=sketchpod
```

## Exporting images from OpenShift
This tool has also support for exporting images from internal OpenShift Docker registry.
First you need to secure and expose internal registry using route. Instructions on how to
setup this are in [official OpenShift documentation](https://docs.openshift.org/latest/install_config/install/docker_registry.html#exposing-the-registry)

Arguments related to exporting images:
 - `--export-images` - Which images should be exported from OpenShift. Options are:
                     "all", "internal", "none".
   - *all* - pulls all images that are specified in artifacts even if they are not in
             OpenShift internal registry
   - *internal* - pull only images from internal OpenShift Docker registry
   - *none* - no images are pulled (default)
 - `--oc-registry-host` - Host of exposed internal OpenShift Docker registry.
                        (Host of docker-registry route)
 - `--registry-host` - Host of registry where images that were to push images
                     pulled from OpenShift internal registry.
 - `--registry-login` - username ans password for authentication to Docker registry
                      (if it is required)


Following example will pull all images that are used in project and  will push them to `localhost:5000` registry.
```sh
openshift2nulecule --project mlb --output ./myapp --oc-registry-host docker-registry.cdk.10.2.2.2.xip.io --export-images all --registry-host localhost:5000 
```

For testing you might want to skip push stage. You can do this by adding `--skip-push` option.
With this option openshift2nulecule will only pull images to you local docker instance.

# Installation
RPMs: https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/

You can also run `openshift2nulecule` as Docker container (see "Usage" section).


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


## Running as Docker container
Easies way how to run openshift2nulecule as Docker container is to use [Atomic](https://github.com/projectatomic/atomic) tool.

```sh
atomic run tomaskral/openshift2nulecule \
  --project testing \
  --output $HOME/mytest \
  --oc-config=$HOME/.kube/config \
  --oc-registry-host 172.30.22.38:5000 \
  --export-images all \
  --registry-host my_registry:5000
```
When you are running openshift2nulecule from container, you have to always specify path to `oc` configuration file (`--oc-config`)
in most cases setting it to default `$HOME/.kube/config` should be enough.

Example of running openshift2nulecule container without Atomic tool:
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

# Notes

### References
  - Exposing the Registry - https://docs.openshift.org/latest/install_config/install/docker_registry.html#exposing-the-registry
  - Openshift object types - https://docs.openshift.com/enterprise/3.0/cli_reference/basic_cli_operations.html#object-types
