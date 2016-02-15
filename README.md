# OpenShift2Nulecule

This tool is creating new Nulecule application with Kubernetes
artifacts from OpenShift project.


## Limitations
 - Exports only ReplicationControllers, PersistentVolumeClaims, Services
 - Works only for projects that are using Docker Images from public
registeries. If you have images in internal OpenShift Docker registry,
you have to manually export them to accessible registry.

# External dependencies
OpenShift client (`oc`) has to be installed and configured to 
connect to OpenShift server.

# Example
```
openshift2nulecule --output=/path/to/new/myapp --project=myproject
```
This will export whole project `myproject` from OpenShift 
and create new Nulecule application in `/path/to/new/myapp` directory.

# Notes

## Brain Dump
### Required steps
 - Export all artifacts from OpenShift (only k8s compatible)
    - (a) Push images that are in internal OpenShift registry to other registry that will be accessible
        - authenticating to registry
        - pushing images to other registy
    - (b) Expose OpenShift registry [1] and use that
        - exporting registry [1]
        - authenticating to registry
 - Create Nulecule file

### Links
 - [1]  Exposing the Registry - https://docs.openshift.org/latest/install_config/install/docker_registry.html#exposing-the-registry

