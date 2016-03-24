# Full workflow tutorial

This example demonstrates how to export application deployed on Openshift,
to Nulecule specification and then import that application to Kubernetes.

This is a 3 step tutorial:
    1. Deploy a sample application on Openshift.
    2. Export the application using openshift2nulecule.
    3. Import the exported artifacts into Kubernetes using Atomic App.


This has been tested on ADB 1.7.1 as Fedora 23 on local machine

## Deploy Docker registry on your local machine
 1. Run Docker registry on you local machine.
    - `docker run -d -p 5000:5000 --name registry registry:2`


## Start ADB and deploy sample OpenShift application
 1. Clone the ADB repository

    `git clone https://github.com/projectatomic/adb-atomic-developer-bundle.git`

 1. Run OpenShift instance in ADB

    - `cd adb-atomic-developer-bundle/components/centos/centos-openshift-setup`
    - `vagrant up`
    - `vagrant ssh`

 1. Add Docker Registry that runs on your local machine as insecure registry (in ADB box)
     
    - `sudo vi /etc/sysconfig/docker`
    - Add your local machine's Docker registry (which was started in the first step) by appending `--insecure-registry 10.1.2.1:5000` to `INSECURE_REGISTRY`
    - `sudo systemctl restart docker`
    - `export MY_REGISTRY=10.1.2.1:5000`
    
 1. Deploy MLB Parks sample application on OpenShift 

    - `oc login` (username: openshift-dev password: devel)
    - `oc new-project mlbparks`
    - `oc create -f https://raw.githubusercontent.com/gshipley/openshift3mlbparks/master/mlbparks-template.json`
    - `oc new-app mlbparks`
    - `oc get builds -w`
    - Wait for mlbarks build to complete.

        ```
        NAME         TYPE      FROM          STATUS     STARTED         DURATION
        mlbparks-1   Source    Git@d63267b   Complete   4 minutes ago   4m6s
        ```


## Use Openshift2Nulecule to export sample application
 1. Install Openshift2Nulecule
    - Add ADB testing repo (required only for ADB 1.7.0)
        ```
        sudo sh -c "cat > /etc/yum.repos.d/centos7-adb-cbs-test.repo <<EOF
        [centos7-adb-cbs-test]
        name=CentOS-$releasever - ADB CBS Testing
        baseurl=https://cbs.centos.org/repos/atomic7-adb-common-testing/x86_64/os/
        gpgcheck=0
        enabled=1
        EOF
        "
        ```

    - install openshift2nulecule

       `sudo yum install openshift2nulecule`

 1. Get address of OpenShift internal Docker registry 
     
    ```
    export OC_REGISTRY=$(sudo oc --config /var/lib/openshift/openshift.local.config/master/admin.kubeconfig get svc docker-registry -o template --template="{{ .spec.clusterIP }}"):5000
    ```

 1. Export mlbpark project as Nulecule application
    ```
    openshift2nulecule --project mlbparks --output ./mlb --oc-registry-host $OC_REGISTRY --export-images all --registry-host $MY_REGISTRY
    ```

 1. Edit mlbpark Nulecule artifact 
    
    This step is because of issue [#117](https://github.com/projectatomic/adb-atomic-developer-bundle/issues/117) in ADB.

    Find and modify replication controller for mongodb.

    - `vi mlb/artifacts/kubernetes/mongodb-1-ReplicationController.json`
    - find "volumeMounts" field in mongodb container and remove that.

 1. Build Docker container with Nulecule application.

    - `docker build -t $MY_REGISTRY/mlbparks-atomicapp mlb`

 1. Push Docker container with Nulecule application to local registry.
    - `docker push $MY_REGISTRY/mlbparks-atomicapp`
    


## Run exported Nulecule application on Kubernetes
 1. Run Kubernetes instance in ADB
   - `cd components/centos/centos-k8s-singlenode-setup`
   - `vagrant up`
   - `vagrant ssh`

 1. Add Docker Registry on you local machine as insecure
     
    - `sudo vi /etc/sysconfig/docker`
    - Change line `# INSECURE_REGISTRY='--insecure-registry '` to `INSECURE_REGISTRY='--insecure-registry 10.1.2.1:5000'`
    - `sudo systemctl restart docker`

 1. Run mlbparks Nulecule  app on Kubernetes.
    - `atomic  run 10.1.2.1:5000/mlbparks-atomicapp`

 1.  Test it
      - `export MLB_SVC_IP=$(kubectl  get svc mlbparks -o template --template="{{ .spec.clusterIP }}")`
      - `curl $MLB_SVC_IP:8080`


## Run exported Nulecule application on OpenShift
 1. Run new instance of ADB/CDK with OpenShift, or use old one.

 1. Add Docker Registry that runs on your local machine as insecure registry (in ADB box)
    (only if you are using new OpenShift ADB/CDK instance)
    - `sudo vi /etc/sysconfig/docker`
    - Change line `# INSECURE_REGISTRY='--insecure-registry '` to `INSECURE_REGISTRY='--insecure-registry 10.1.2.1:5000'`
    - `sudo systemctl restart docker`

 1. Run mlbparks Nulecule app on OpenShift
    - `oc new-project mlbimport`
    - `atomic run 10.1.2.1:5000/mlbparks-atomicapp --provider=openshift --providerconfig=/home/vagrant/.kube/config --namespace=mlbimport`

 1.  Test it
      - `export MLB_SVC_IP=$(oc get svc mlbparks -o template --template="{{ .spec.clusterIP }}")`
      - `curl $MLB_SVC_IP:8080`
