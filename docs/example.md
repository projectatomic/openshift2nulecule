# Full workflow tutorial

This example demonstrates how to export application deployed on Openshift
to Nulecule specification and then import that application to Kubernetes and/or OpenShift.

This is a 3 step tutorial:
    1. Deploy a sample application on Openshift.
    2. Export the application using openshift2nulecule.
    3. Import the exported artifacts into Kubernetes using Atomic App.


This has been tested on ADB 1.8.0 with Fedora 23 on host machine

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

    This expects that you kept IP settings in Vagrent file on default `10.1.2.2`
    If not you will have to change all IP addresses in this tutorial accordingly.
     
    - `sudo vi /etc/sysconfig/docker`
    - Change line `# INSECURE_REGISTRY='--insecure-registry '` to `INSECURE_REGISTRY='--insecure-registry 10.1.2.1:5000'`
    - `sudo systemctl restart docker`
    - `export MY_REGISTRY=10.1.2.1:5000`
    
 1. Deploy MLB Parks sample application on OpenShift 

    - You should already be logged in as openshift-dev user. You can verify that by running `oc whoami`
    - `oc new-project mlbparks`
    - `oc new-app -f https://raw.githubusercontent.com/gshipley/openshift3mlbparks/master/mlbparks-template.json`
    - `oc get builds -w`
    - Wait for mlbarks build to complete. When it is done status should be `Completed`

        ```
        NAME         TYPE      FROM          STATUS     STARTED         DURATION
        mlbparks-1   Source    Git@d63267b   Complete   4 minutes ago   4m6s
        ```


## Use Openshift2Nulecule to export sample application
 1. Install Openshift2Nulecule

    This step is **not** required if you are using CDK 2.0. OpenShift2Nulecule should be already installed in CDK box.

    - Add [tkral/openshift2nulecle](https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/) Copr repository
      
      `sudo sh -c "curl  https://copr.fedorainfracloud.org/coprs/tkral/openshift2nulecle/repo/epel-7/tkral-openshift2nulecle-epel-7.repo > /etc/yum.repos.d/tkral-openshift2nulecle-epel-7.repo"`

    - install openshift2nulecule

       `sudo yum install openshift2nulecule`


 1. Get address of OpenShift internal Docker registry 

    ```
    export OC_REGISTRY=$(sudo oc --config /var/lib/openshift/openshift.local.config/master/admin.kubeconfig get svc docker-registry -o template --template="{{ .spec.clusterIP }}"):5000
    ```

 1. Export mlbpark project as Nulecule application

    ```
    openshift2nulecule --project mlbparks --output ./mlb  --export-images all --oc-registry-host $OC_REGISTRY --registry-host $MY_REGISTRY
    ```
    This command is going to export all objects in `mlbparks` project as single Nulecule application.
    All images that are used in OpenShift objects are going to be pulled to local Docker instance, and then pushed to your 
    docker registry specified by `--registry-host` option.

    Meaning of each option:
    - `--project mlbparks` - export project named `mlbparks`
    - `--output ./mlb` - create Nulecule application in `mlb` directory in current path.
    - `--export-images all` - export all Docker images that are used in OpenShift objects
    - `--oc-registry-host $OC_REGISTRY` - IP address or hostname of OpenShift's internal registry
    - `--regsitry-host $MY_REGISTRY` -  IP address or hostname of your registry where all exported images from OpenShift will be pushed.

 1. Build Atomic App container with Nulecule application.

    - `docker build -t $MY_REGISTRY/mlbparks-atomicapp mlb`

 1. Push Docker container with Nulecule application to Docker registry running on your host machine.
    - `docker push $MY_REGISTRY/mlbparks-atomicapp`
    


## Run exported Nulecule application on Kubernetes
 1. Run Kubernetes instance in ADB
   - `cd components/centos/centos-k8s-singlenode-setup`
   - `vagrant up`
   - `vagrant ssh`

 1. Add Docker Registry on you local machine as insecure
    Add your local machine's Docker registry (which was started in the first step).
    - `sudo vi /etc/sysconfig/docker`
    - Change line `# INSECURE_REGISTRY='--insecure-registry '` to `INSECURE_REGISTRY='--insecure-registry 10.1.2.1:5000'`
    - `sudo systemctl restart docker`


 1. Label /var/lib/kubelet/pods as `svirt_sandbox_file_t`
    This step is because of bug [#117](https://github.com/projectatomic/adb-atomic-developer-bundle/issues/117) in ADB 
    - `chcon -Rt svirt_sandbox_file_t /var/lib/kubelet/pods`

 1. Run mlbparks Nulecule  app on Kubernetes.
    - `sudo -E atomic run 10.1.2.1:5000/mlbparks-atomicapp`

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
    - `sudo -E atomic run 10.1.2.1:5000/mlbparks-atomicapp --provider=openshift --providerconfig=/home/vagrant/.kube/config --namespace=mlbimport`
 1. Wait for mlbparks build to finish
    You can see log of build on web console, or in you terminal using this command `oc build-logs mlbparks-1`.

    Because of OpenShift Origin issue [#4518](https://github.com/openshift/origin/issues/4518) and Atomic App issue [#669](https://github.com/projectatomic/atomicapp/issues/669) build might fail on `Error: build error: Failed to push image. ....... : no basic auth credentials`. Just starting build again with `oc start-build mlbparks` should be enought to fix this.
    

 1.  Test it
      - `export MLB_SVC_IP=$(oc get svc mlbparks -o template --template="{{ .spec.clusterIP }}")`
      - `curl $MLB_SVC_IP:8080`
