%define name openshift2nulecule
%define version 0.0.2
%define release 1

Summary: Tool to create Nulecule from OpenShift
Name: %{name}
Version: %{version}
Release: %{release}
License: LGPL3
BuildArch: noarch
Url: https://github.com/kadel/openshift2nulecule
Source0: %{name}-%{version}.tar.gz

BuildRequires: python2-devel >= 2.4
BuildRequires: python-pip
Requires: python-requests
Requires: python-anymarkup
Requires: python-ipaddress


%description
Tool for creating Nulecule application from OpenShift project

%prep
%autosetup -n %{name}-%{version}

%build
#python2 setup.py build
%py2_build

%install
#python2 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
%py2_install

%clean
rm -rf $RPM_BUILD_ROOT

#files -f INSTALLED_FILES
#defattr(-,root,root)
%files -n %{name}
%{python2_sitelib}/*
%doc README.md CHANGELOG.md
%{_bindir}/openshift2nulecule

%changelog
* Mon Feb 15 2016 Tomas Kral <tkral@redhat.com> 0.0.2-1
- stop exporting pods
- show warning when exporting ReplicatinController with image from internal registry

* Thu Jul 21 2016 Tomas Kral <tkral@redhat.com> 0.0.1-1
- initial version

