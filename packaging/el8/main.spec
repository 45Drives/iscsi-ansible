Name: ::package_name::
Version: ::package_version::
Release: ::package_build_version::%{?dist}
Summary: ::package_description_short::
License: ::package_licence::
URL: ::package_url::
Source0: %{name}-%{version}.tar.gz
BuildArch: ::package_architecture_el::
Requires: ::package_dependencies_el::

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
::package_title::
::package_description_long::

%prep
%setup -q

%build

%install
make DESTDIR=%{buildroot} install

%files
/usr/share/iscsi-ansible/*

%changelog
* Mon Nov 11 2024 Brett Kelly <bkelly@45drives.com> 1.0.2-1
- refresh dnf cache before checking for new kernels
- ensure kernel-devel is installed before building scst
* Thu Jul 25 2024 Brett Kelly <bkelly@45drives.com> 1.0.1-1
- initial package build
- updated pcs config options
* Wed Jul 24 2024 Brett Kelly <bkelly@45drives.com> 1.0.0-1
- initial package build