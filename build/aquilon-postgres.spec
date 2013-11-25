Summary: Aquilon with PostgreSQL backend
Name: aquilon-postgresql
Version: 1.0.0
Release: 1
License: Apache
Group: System Environment/Daemons
URL: http://quattor.org
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch
Requires: aquilon, python-psycopg2

%description

Meta-package for installing Aquilon with a PostgreSQL backend

%prep

%build

%install

%clean
rm -rf $RPM_BUILD_ROOT


%files


%changelog
