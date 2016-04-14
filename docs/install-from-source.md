Installation from source
========================

Usage Installation
------------------

- Clone the `openshift2nulecule` repository

```bash
$ git clone https://github.com/projectatomic/openshift2nulecule.git
$ cd openshift2nulecule
```

- Start a installation

```bash
$ python setup.py install
```


Developer Installation
----------------------

- Pre-requisite installation

```bash
$ sudo pip install virtualenvwrapper
$ echo 'source virtualenvwrapper.sh' >> ~/.bashrc
$ source virtualenvwrapper.sh
```

- Create a virtual environment

```bash
$ mkvirtualenv o2n
```

- Clone the `openshift2nulecule` repository

```bash
$ git clone https://github.com/projectatomic/openshift2nulecule.git
$ cd openshift2nulecule
```

- Start a developer installation

```bash
$ python setup.py develop
```

- Everytime you start working you can activate the virtual environment as

```bash
$ workon o2n
```

- Deactivate the virtual environment

```bash
$ deactivate
```
