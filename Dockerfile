FROM fedora:23

MAINTAINER Tomas Kral <tkral@redhat.com>

LABEL RUN="docker run -it --rm \${OPT1} --privileged -v /var/run/docker.sock:/var/run/docker.sock -v /:/host --net=host --name \${NAME} \${IMAGE}"

ADD requirements.txt ./

# requires python-docker-py >= 1.6.0 that is only in testing
RUN dnf install -y --setopt=tsflags=nodocs --enablerepo=updates-testing $(sed s/^/python-/ requirements.txt) && \
    dnf install -y --setopt=tsflags=nodocs docker && \
    dnf clean all

ENV PYTHONPATH  /opt/openshift2nulecule/

ENTRYPOINT ["/usr/bin/python", "/opt/openshift2nulecule/openshift2nulecule/cli/main.py"]

ADD . /opt/openshift2nulecule

