FROM centos:7

MAINTAINER Tomas Kral <tkral@redhat.com>

LABEL RUN="docker run -it --rm \${OPT1} --privileged --user=\${SUDO_UID}:\${SUDO_GID} -v /:/host --net=host --name \${NAME} \${IMAGE}"

ADD requirements.txt ./

RUN yum install -y epel-release && \
    yum install -y --setopt=tsflags=nodocs docker && \
    yum install -y --setopt=tsflags=nodocs $(sed s/^/python-/ requirements.txt) && \
    yum clean all

ENV PYTHONPATH  /opt/openshift2nulecule/

ENTRYPOINT ["/usr/bin/python", "/opt/openshift2nulecule/openshift2nulecule/cli/main.py"]

ADD . /opt/openshift2nulecule

