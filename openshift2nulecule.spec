%global commit0 61dc8957ce9b7b078a3848f89a174a46d6334335
%global gittag0 GIT-TAG
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

Summary:       Tool to create Nulecule based application from OpenShift
Name:          openshift2nulecule
Version:       0.0.2
Release:       3%{?dist}
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
* Tue Mar 1 2016 Lalatendu Mohanty <lmohanty@redhat.com> 0.0.2-3
- Refactored the specfile

* Wed Feb 17 2016 Tomas Kral <tkral@redhat.com> 0.0.2-2
- update source - direct link to github

* Mon Feb 15 2016 Tomas Kral <tkral@redhat.com> 0.0.2-1
- stop exporting pods
- show warning when exporting ReplicatinController with image from internal registry

* Thu Jan 21 2016 Tomas Kral <tkral@redhat.com> 0.0.1-1
- initial version

