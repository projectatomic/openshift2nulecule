#!/bin/bash
set -e

ORIGIN_CONTAINER="o2n-test-origin"

TMP="/tmp/o2n-tests"
mkdir -p /tmp/o2n-tests
OC="$TMP/oc"
OPENSHIFT_REGISTRY_FILE="$TMP/OPENSHIFT_REGISTRY"

LOCAL_REGISTRY_PORT=5555
LOCAL_REGISTRY_CONTAINER="$ORIGIN_CONTAINER-registry"


start_local_registry() {
    docker run -d  --name=$LOCAL_REGISTRY_CONTAINER \
        -p $LOCAL_REGISTRY_PORT:5000 \
        registry:2
}


stop_local_registry() {
    docker stop $LOCAL_REGISTRY_CONTAINER || true
    docker rm $LOCAL_REGISTRY_CONTAINER  || true
}

start_openshift() {

    # start opensfhit
    docker run -d --name=$ORIGIN_CONTAINER \
            --privileged --pid=host --net=host \
            -v /:/rootfs:ro -v /var/run:/var/run:rw -v /sys:/sys -v /var/lib/docker:/var/lib/docker:rw \
            -v /var/lib/origin/openshift.local.volumes:/var/lib/origin/openshift.local.volumes \
            openshift/origin start

    # copy oc binary out of the container
    # cp sometimes fails on "operation not permitted" this is why || true and than check by ls
    docker cp $ORIGIN_CONTAINER:/usr/bin/openshift $OC || true
    ls -lah $OC

    echo "[INFO] Waiting for openshift to start."
    i=0
    until curl -k https://localhost:8443 > /dev/null 2>&1 ; do
        echo -n "."
        sleep 5s
        # do not wait forever
        i=$((i+1))
        if [ "$i" -ge 24 ]; then
            echo ""
            echo "[ERROR] Timeout while waiting for OpenShift to start."
            exit
        fi
    done
    echo "[INFO] OpenShift is running."



    # run oc client in container
    run_oc()  {
        echo "$@"
        docker exec -it $ORIGIN_CONTAINER $@
    }

    # login as system admin
    sleep 1s
    run_oc oc login -u system:admin

    # deploy registry
    run_oc oadm registry --credentials=./openshift.local.config/master/openshift-registry.kubeconfig
    REGISTRY_SERVICE_IP=$(docker exec -it $ORIGIN_CONTAINER oc get svc/docker-registry -o template --template='{{ .spec.clusterIP }}')
    REGISTRY_SERVICE_PORT=$(docker exec -it $ORIGIN_CONTAINER oc get svc/docker-registry -o template --template='{{ (index .spec.ports 0).port }}')

    echo "$REGISTRY_SERVICE_IP:$REGISTRY_SERVICE_PORT" > $OPENSHIFT_REGISTRY_FILE

    echo "[INFO] OpenShift Docker registry service $REGISTRY_SERVICE_IP:$REGISTRY_SERVICE_PORT" 


    echo "[INFO] Importing templates and image streams"
    ose_tag=ose-v1.2.0
    template_list=(
        # Image streams
        https://raw.githubusercontent.com/openshift/origin/master/examples/image-streams/image-streams-rhel7.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/jboss-image-streams.json
        # DB templates
        https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mongodb-ephemeral-template.json
        https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mongodb-persistent-template.json
        https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mysql-ephemeral-template.json
        https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mysql-persistent-template.json
        https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/postgresql-ephemeral-template.json
        https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/postgresql-persistent-template.json
        # Jenkins
        https://raw.githubusercontent.com/openshift/origin/master/examples/jenkins/jenkins-ephemeral-template.json
        https://raw.githubusercontent.com/openshift/origin/master/examples/jenkins/jenkins-persistent-template.json
        # Node.js
        https://raw.githubusercontent.com/openshift/nodejs-ex/master/openshift/templates/nodejs-mongodb.json
        https://raw.githubusercontent.com/openshift/nodejs-ex/master/openshift/templates/nodejs.json
        # EAP
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-amq-persistent-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-amq-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-basic-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-https-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mongodb-persistent-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mongodb-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mysql-persistent-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mysql-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-postgresql-persistent-s2i.json
        https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-postgresql-s2i.json
    )
    for template in ${template_list[@]}; do
        run_oc oc create -f $template -n openshift
    done

}


deploy_apps() {
    # login as normal user
    $OC login --insecure-skip-tls-verify=true -u test-user -p test-user https://127.0.0.1:8443


    $OC new-project mlbparks
    $OC create -f https://raw.githubusercontent.com/gshipley/openshift3mlbparks/master/mlbparks-template.json
    $OC new-app mlbparks

    $OC new-project rubyhello
    $OC new-app centos/ruby-22-centos7~https://github.com/openshift/ruby-hello-world.git

    # wait for build to finish
    mlbstatus="None"
    rubystatus="None"
    i=0
    echo "[INFO] Waiting for builds to finish"
    until [[ "$mlbstatus" == "Complete" && "$rubystatus" == "Complete" ]]; do
    #until [[ "$rubystatus" == "Complete" ]]; do
        mlbstatus=$(docker exec -it $ORIGIN_CONTAINER oc -n mlbparks get builds -o template --template "{{if .items }}{{ (index .items 0).status.phase }}{{end}}")
        rubystatus=$(docker exec -it $ORIGIN_CONTAINER oc -n rubyhello get builds -o template --template "{{if .items }}{{ (index .items 0).status.phase }}{{end}}")

        #docker exec -it $ORIGIN_CONTAINER oc get event
        #docker exec -it $ORIGIN_CONTAINER oc logs ruby-hello-world-1-build
        echo "mlbparks  = $mlbstatus"
        echo "rubyhello = $rubystatus"
        sleep 10s
        
        i=$((i+1))
        if [ "$i" -ge 120 ]; then
            echo ""
            echo "[ERROR] Timeout while waiting for build to finish"
            echo "$i"
            #exit
        fi
    done
}


stop_openshift() {
    docker stop $ORIGIN_CONTAINER || true
    docker rm $ORIGIN_CONTAINER || true
}




run_tests() {
    OPENSHIFT_REGISTRY=$(cat $OPENSHIFT_REGISTRY_FILE)

    deploy_apps

    $OC login --insecure-skip-tls-verify=true -u test-user -p test-user https://127.0.0.1:8443

    openshift2nulecule --output rubyhello-exported \
        --project rubyhello \
        --oc $OC \
        --export-images all \
        --oc-registry-host $OPENSHIFT_REGISTRY \
        --registry-host 127.0.0.1:$LOCAL_REGISTRY_PORT

    docker build  -t 127.0.0.1:$LOCAL_REGISTRY_PORT/rubyhello-atomicapp rubyhello-exported
    docker push 127.0.0.1:$LOCAL_REGISTRY_PORT/rubyhello-atomicapp


    openshift2nulecule --output mlbparks-exported \
        --project mlbparks \
        --oc $OC \
        --export-images all \
        --oc-registry-host $OPENSHIFT_REGISTRY \
        --registry-host 127.0.0.1:$LOCAL_REGISTRY_PORT

    docker build  -t 127.0.0.1:$LOCAL_REGISTRY_PORT/mlbparks-atomicapp mlbparks-exported
    docker push 127.0.0.1:$LOCAL_REGISTRY_PORT/mlbparks-atomicapp

    stop_openshift
    start_openshift

    $OC login --insecure-skip-tls-verify=true -u test-user -p test-user https://127.0.0.1:8443

    $OC new-project mlbparks-import

    sudo atomic run 127.0.0.1:$LOCAL_REGISTRY_PORT/mlbparks-atomicapp  \
        --provider=openshift \
        --namespace=mlbparks-import \
        --providerconfig=$HOME/.kube/config

    $OC new-project rubyhello-import
 
    sudo atomic run 127.0.0.1:$LOCAL_REGISTRY_PORT/rubyhello-atomicapp  \
        --provider=openshift \
        --namespace=rubyhello-import \
        --providerconfig=$HOME/.kube/config
}


if [[ $1 == "prepare" ]]; then
    start_openshift
    start_local_registry
elif [[ $1 == "clean" ]]; then
    stop_local_registry
    stop_openshift
elif [[ $1 == "run_tests" ]]; then
    run_tests
else
    echo "Usage: $0 [prepare | clean | run_tests ]"
fi


