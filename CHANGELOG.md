## openshift2nulecule 0.1.0 (05-04-2016)
- added OpenShift artifacts to exported Nulecule #6
- added `--skip-push` option #36
- updated docs, and added docs/example.md with step by step tutorial #28
- removed docker-py as dependency (using docker cli instead see) #21
- added `--atomicapp-ver` to specify atomicapp version for Dockerfile #26

## openshift2nulecule 0.0.4 (03-03-2016)
- bugfix release for 0.0.3

## openshift2nulecule 0.0.3 (03-02-2016)
- ability to export images from  internal OpenShift registry.
  Options to configure that: `--oc-registry-host`, `--export-images`, `--registry-host`, `--registry-login`
- add Dockerfile
- finding path to `oc` binary 
- detection if program is running inside container (using /host)

## openshift2nulecule 0.0.2 (02-15-2016)
- stop exporting pods
- show warning when exporting ReplicatinController with image from internal registry

## openshift2nulecule 0.0.1 (01-21-2016)
Initial version
