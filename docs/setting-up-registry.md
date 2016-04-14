# Running private docker registry for o2n
This is a manual for running and setting up private Docker Registry on different platforms (Linux, Mac, Windows) for use with OpenShift2Nulecule.

## Running the registry
You can choose from different images:
 - registry:2 (library/registry:2)
 - centos/registry:2

##### Notes
 - All registry images with version __<2__ are from old sources and __deprecated__ by Docker.
 - The __:z__/__:Z__ are docker options for automatically setting up SELinux on volume mounts for you. These will not work on sshfs mounts but there is a workaround mentioned in following section.

### Natively (Linux)
```bash
sudo mkdir /var/lib/registry
sudo docker run -d -p 5000:5000 --name registry -v /var/lib/registry:/var/lib/registry:Z centos/registry:2
```
 - If you are running Docker Registry natively on Linux platform without SELinux you don't have to (and probably shouldn't) use the __:z__/__:Z__ flags.

### Inside ADB/CDK (Mac, Windows, Linux)
Please be aware if you run Docker Registry in ADB/CDK box all data are not persistent and will be lost after `vagrant destroy`. You will most likely want to use a separate ADB/CDK instance for running a docker registry and possibly setting up persistant storage as described by the next chapter.

```bash
vagrant up
vagrant ssh
sudo mkdir /var/lib/registry
docker run -d -p 5000:5000 --name registry -v /var/lib/registry:/var/lib/registry:Z centos/registry:2
```

### Inside ADB/CDK (Mac, Windows, Linux) with persistent storage (using sshfs)
Before running Docker Registry inside a box you can mount a directory from host into ADB/CDK to set up persistant storage (folder). It will survive `vagrant destroy`.

0) [Windows only] Install openssh via cygwin to get sftp-server. You can find more information in plugin's [documentation](https://github.com/dustymabe/vagrant-sshfs/blob/master/README.md).

1) Install [vagrant-sshfs](https://github.com/dustymabe/vagrant-sshfs) plugin
```bash
vagrant plugin install vagrant-sshfs
```
2) Edit your Vagrantfile and add
```vagrant
config.vm.synced_folder "/path/on/host/registry-data", "/var/lib/registry", type: "sshfs"
```
For more options please see plugin's [documentation](https://github.com/dustymabe/vagrant-sshfs/blob/master/README.md).

3) Run Docker Registry
```bash
vagrant up
vagrant ssh
sudo setsebool -P virt_sandbox_use_fusefs 1  # allow docker volumes over sshfs
docker run -d -p 5000:5000 --name registry -v /var/lib/registry:/var/lib/registry centos/registry:2
```

## Setting up private registry on target (developement) platform
At this point you should have running Docker Registry (either natively or in ADB/CDK). Since we did not set up any certificates it is insecure and you need to configure your docker client to allow using it.

On your host/developent machine edit your docker configuration
 - Linux (Fedora, CentOS , RHEL)
 
 ```bash
 echo 'INSECURE_REGISTRY=\'--insecure-registry 10.1.2.2:5000\'' >> /etc/sysconfig/docker
 ```
 - Other platforms - Set it up it in similar fashion
  * TODO: Add set up steps for Mac and Windows. Please contribute if you are using one of these platforms.

Supposing:
 - 10.1.2.2 - IP of machine/box running Docker Registry
 - 5000 - port of Docker Registry
