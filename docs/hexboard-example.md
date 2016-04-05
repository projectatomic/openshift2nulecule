Hexboard application end to end tutorial
========================================

These steps will get you through 

1. Deploy Hexboard application on OpenShift instance.
2. Export that app, make some changes to the artifacts.
3. Start another OpenShift instance and import previously exported artifacts.

Note: Here 'host machine' means the physical machine.


* Setup Docker registry on your host machine.
    
    ```bash
    $ sudo docker run -d -p 5000:5000 --name registry registry:2
    ```


* Start an OpenShift Instance using the Vagrantfile provided specifically to run OpenShift

    * Clone [ADB](https://github.com/projectatomic/adb-atomic-developer-bundle) repository
        ```bash
        $ git clone https://github.com/projectatomic/adb-atomic-developer-bundle.git
        ```

    * Start the OpenShift instance using `Vagrantfile` that is in the repository

        ```bash
        $ cd adb-atomic-developer-bundle/components/centos/centos-openshift-setup
        $ vagrant up
        $ vagrant ssh
        ```
    * Add information of `docker-registry` running on host machine
    
        ```bash
        $ echo "INSECURE_REGISTRY='--insecure-registry 10.1.2.1:5000'" | sudo tee /etc/sysconfig/docker
        $ sudo systemctl restart docker
        $ export MY_REGISTRY=10.1.2.1:5000
        ```

    * Deploy the application on OpenShift instance.
        
        First login using username: "openshift-dev" and password: "devel"
        ```bash
        $ oc login
        ```
        Create new-project and deploy application from the template.
        ```bash
        $ oc new-project hexboard
        $ oc new-app -f https://raw.githubusercontent.com/2015-Middleware-Keynote/hexboard/master/app_template.json -p ACCESS_TOKEN=$(oc whoami -t)
        ```
        This has deployed application, but will take some time to work because internally the app is being built.
        ```bash
        $ watch oc get builds
        NAME          TYPE      FROM             STATUS    STARTED          DURATION
        hexboard-1    Source    Git@master       Running   10 seconds ago   10s
        sketchpod-1   Source    Git              Running   10 seconds ago   10s
        ```
        After the `STATUS` changes to `Complete` you can exit out of it using `Ctrl + C`.
        Now check if the pods are running all good.
        ```bash
        $ oc get pods
        NAME                READY     STATUS      RESTARTS   AGE
        hexboard-1-build    0/1       Completed   0          3m
        hexboard-1-wlmhg    1/1       Running     0          1m
        sketchpod-1-build   0/1       Completed   0          3m
        sketchpod-1-ep2pk   1/1       Running     0          1m

        ```
        The app is running good.
        
* Export the working application.

    * Export the application
    
        ```bash
        $ cd ~
        $ openshift2nulecule --project hexboard --output ~/hexboard
        ```        
    
    * Edit the application artifacts
    
        Edit the Environment Variable  `"ACCESS_TOKEN"`'s `"value"` field and set it to `$access_token` in `artifacts/openshift/hexboard-DeploymentConfig.json` as follows:
        ```bash
        {
            "name": "ACCESS_TOKEN",
            "value": "$access_token"
        }
        ```

        Make sure your `Nulecule` file looks like this:

        ```bash
        graph:
        - artifacts:
            kubernetes:
            - file://artifacts/kubernetes/hexboard-Service.json
            - file://artifacts/kubernetes/sketchpod-Service.json
            - file://artifacts/kubernetes/hexboard-1-ReplicationController.json
            - file://artifacts/kubernetes/sketchpod-1-ReplicationController.json
            openshift:
            - file://artifacts/openshift/hexboard-ImageStream.json
            - file://artifacts/openshift/sketchpod-ImageStream.json
            - file://artifacts/openshift/hexboard-Service.json
            - file://artifacts/openshift/sketchpod-Service.json
            - file://artifacts/openshift/hexboard-DeploymentConfig.json
            - file://artifacts/openshift/sketchpod-DeploymentConfig.json
            - file://artifacts/openshift/hexboard-BuildConfig.json
            - file://artifacts/openshift/sketchpod-BuildConfig.json
          name: hexboard
          params:
            - name: access_token
              description: Access token of the user found using (oc whoami -t)
        id: hexboard
        metadata:
          name: hexboard
        specversion: 0.0.2
        ```
        This particular application relies on the user's `ACCESS_TOKEN`, so while deploying the application for the first time using template you may have noticed that we have provided `ACCESS_TOKEN`. Now while deploying the application on some other OpenShift instance, we need to some how feed the new `ACCESS_TOKEN` to the application. So we have introduced a variable `$access_token` in `artifacts/openshift/hexboard-DeploymentConfig.json` and in `Nulecule`, so now while deploying the app again on any OpenShift instance this token will be inserted on the fly via interactive question.
    
    * Make a Docker image of this application and push it to host-machine repository
    
        ```bash
        $ docker build -t $MY_REGISTRY/hexboard-atomicapp ~/hexboard
        $ docker push $MY_REGISTRY/hexboard-atomicapp
        ```
        
    * Stop this OpenShift instance
    
        ```bash
        $ logout
        $ vagrant halt
        ```
        
* Start another OpenShift Instance using the Vagrantfile provided specifically to run OpenShift

    * Clone ADB repository, in some other location, than previous one.
        ```bash
        $ git clone https://github.com/projectatomic/adb-atomic-developer-bundle.git
        ```

    * Start the OpenShift instance using `Vagrantfile` that is in the repository

        ```bash
        $ cd adb-atomic-developer-bundle/components/centos/centos-openshift-setup
        $ vagrant up
        $ vagrant ssh
        ```
    * Add information of `docker-registry` running on host machine
    
        ```bash
        $ echo "INSECURE_REGISTRY='--insecure-registry 10.1.2.1:5000'" | sudo tee /etc/sysconfig/docker
        $ sudo systemctl restart docker
        $ export MY_REGISTRY=10.1.2.1:5000
        ```

    * Deploy the application on OpenShift instance.
        
        First login using username: "openshift-dev" and password: "devel"
        ```bash
        $ oc login
        ```
        Create new-project and deploy application from the exported container.
        ```bash
        $ oc new-project hexboard-imported
        ```
        Before deploying the actual app, get the access-token as:
        ```bash
        $ oc whoami -t
        ```
        Deploy the application
        ```bash
        $ sudo -i
        $ atomic run $MY_REGISTRY/hexboard-atomicapp --provider=openshift --providerconfig=/home/vagrant/.kube/config --namespace=hexboard-imported
        ```
        
    * Verify app is deployed by opening browser and visiting https://10.1.2.2:8443/console/ but like previous deployment it will take some time to see it working, because it will build the app first.
