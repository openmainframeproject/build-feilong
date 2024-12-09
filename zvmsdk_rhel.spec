# Copyright 2024 Contributors to the Open Mainframe Project.

%define name zvmsdk

Summary: IBM z/VM cloud connector
Name: %{name}
Version: 1.4.0
Release: 1
Source: zvmsdk.tar.gz
Source1: vhost.config
Vendor: IBM
License: ASL 2.0
BuildArch: noarch
Group: System/tools
Autoreq: no
Requires: python3 >= 2.7, python3-netaddr >= 0.7.5, python3-jwt >= 1.0.1, python3-requests >= 2.6.0, python3-routes >= 2.2, python3-webob >= 1.2.3, python3-jsonschema >= 2.3.0, python3-six >= 1.9.0, zthin >= 3.1.0, httpd >= 2.4.0, python3-mod_wsgi, python3-jinja2, s390utils
BuildRoot: %{_tmppath}/zvmsdk
Prefix: /opt/zvmsdk
BuildRequires: python3-setuptools

%description
The System z/VM cloud connector is a set of APIs to be used
by external API consumer.

%prep
tar -zxvf ../SOURCES/zvmsdk.tar.gz -C ../BUILD/ --strip 1
cp ../SOURCES/vhost.config ../BUILD/zvmsdk.conf

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES

mkdir -p %{buildroot}/var/lib/zvmsdk
mkdir -p %{buildroot}/etc/zvmsdk
mkdir -p %{buildroot}/var/log/zvmsdk
mkdir -p %{buildroot}/var/opt/zvmsdk
mkdir -p %{buildroot}/etc/httpd/conf.d

cp zvmsdklogs %{buildroot}/var/opt/zvmsdk
cp ../BUILD/zvmsdk.conf %{buildroot}/etc/httpd/conf.d/

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)
%dir %attr(0755, zvmsdk, zvmsdk) /etc/zvmsdk
%dir %attr(0755, zvmsdk, zvmsdk) /var/log/zvmsdk
%dir %attr(0755, zvmsdk, zvmsdk) /var/opt/zvmsdk
%dir %attr(0755, zvmsdk, zvmsdk) /var/lib/zvmsdk

%config(noreplace) /var/opt/zvmsdk/zvmsdklogs
%config(noreplace) /etc/httpd/conf.d/zvmsdk.conf

%pre
/usr/bin/getent passwd zvmsdk >/dev/null || /usr/sbin/useradd -r -d /var/lib/zvmsdk -m -U zvmsdk -s /bin/bash 2>/dev/null 1>&2

%post
chown zvmsdk /var/lib/zvmsdk/setupDisk
chgrp zvmsdk /var/lib/zvmsdk/setupDisk
chown zvmsdk /etc/zvmsdk/*
chgrp zvmsdk /etc/zvmsdk/*

if [ ! -f "/etc/logrotate.d/zvmsdklogs" ]; then
    cp /var/opt/zvmsdk/zvmsdklogs /etc/logrotate.d
fi

# call zvmsdk-gentoken to create init token
if [ ! -f "/etc/zvmsdk/token.dat" ]; then
  zvmsdk-gentoken
  chown zvmsdk /etc/zvmsdk/token.dat
  chgrp zvmsdk /etc/zvmsdk/token.dat
  chmod 0600 /etc/zvmsdk/token.dat
else
  echo "Token file already exists"
fi

if systemctl is-active --quiet firewalld; then
    echo "Firewalld is running, opening port 8080"
    firewall-cmd --permanent --add-port=8080/tcp
    firewall-cmd --add-port=8080/tcp
    firewall-cmd --reload
else
    echo "Firewalld is not running, not opening port 8080" >&2
fi

%postun
/usr/bin/getent passwd zvmsdk >/dev/null && userdel zvmsdk 2>/dev/null 1>&2
rm -fr /etc/logrotate.d/zvmsdklogs
