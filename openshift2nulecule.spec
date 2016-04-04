Summary:       Tool to create Nulecule based application from OpenShift
Name:          openshift2nulecule
Version:       0.1.0
Release:       1%{?dist}
License:       GPLV2
BuildArch:     noarch

Url:           https://github.com/projectatomic/%{name}
Source0:       https://github.com/projectatomic/%{name}/archive/v%{version}.tar.gz

BuildRequires: python2-devel >= 2.4
BuildRequires: python-pip
BuildRequires: python >= 2.4
Requires:      python-requests
Requires:      python-anymarkup
Requires:      python-ipaddress
Requires:      docker

%description
openshift2nulecule is a tool to create/export new Nulecule application with Kubernetes artifacts
from OpenShift (V3).

%prep
%setup -q -n %{name}-%{version}

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python2} setup.py build

%install
%{__python2} setup.py install --skip-build --root %{buildroot}

%clean
rm -rf $RPM_BUILD_ROOT

%files -n %{name}
%{python2_sitelib}/*
%doc README.md CHANGELOG.md
%{_bindir}/openshift2nulecule

%changelog
* Wed Apr 5 2016 Tomas Kral <tkral@redhat.com> 0.1.0-1
- Update to 0.1.0
- remove python-docker-py from Requires
- add docker to Requires

* Wed Mar 2 2016 Tomas Kral <tkral@redhat.com> 0.0.4-1
- Update to 0.0.4
- python-docker-py requires >= 1.6.0

* Wed Mar 2 2016 Tomas Kral <tkral@redhat.com> 0.0.3-1
- Update to 0.0.3
- Add python-docker-py dependency

* Tue Mar 1 2016 Lalatendu Mohanty <lmohanty@redhat.com> 0.0.2-3
- Refactored the specfile

* Wed Feb 17 2016 Tomas Kral <tkral@redhat.com> 0.0.2-2
- update source - direct link to github

* Mon Feb 15 2016 Tomas Kral <tkral@redhat.com> 0.0.2-1
- stop exporting pods
- show warning when exporting ReplicatinController with image from internal registry

* Thu Jan 21 2016 Tomas Kral <tkral@redhat.com> 0.0.1-1
- initial version

