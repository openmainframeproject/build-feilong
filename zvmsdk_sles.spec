## Copyright 2024 Contributors to the Open Mainframe Project.

%define name zvmsdk

Summary: IBM z/VM cloud connector
Name: %{name}
Version: 1.4.0
Release: 1
Source: zvmsdk.tar.gz
Vendor: IBM
License: Apache-2.0
BuildArch: noarch
Group: System/tools
Autoreq: no
Requires: python3 >= 2.7, python3-netaddr >= 0.7.5, python3-WebOb >= 1.7.4, python3-PyJWT >= 2.4.0, python3-requests >= 2.6.0, python3-jsonschema >= 2.3.0, python3-six >= 1.9.0, zthin >= 3.1.0, apache2 >= 2.4.0, apache2-mod_wsgi-python3 >= 4.5, python3-Jinja2, python3-Routes, python3-PyYAML
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
find %{buildroot} -name __pycache__ | sed 's!^%{buildroot}!%dir !' >> INSTALLED_FILES
find %{buildroot}/usr/lib/python3.6/site-packages -type d -not -path '*/__pycache__*' | sed 's!^%{buildroot}!%dir !' | sort --unique >> INSTALLED_FILES

mkdir -p %{buildroot}/var/lib/zvmsdk
mkdir -p %{buildroot}/etc/zvmsdk
mkdir -p %{buildroot}/var/log/zvmsdk
mkdir -p %{buildroot}/var/opt/zvmsdk
mkdir -p %{buildroot}/etc/apache2/conf.d

cp zvmsdklogs %{buildroot}/var/opt/zvmsdk
cp ../BUILD/zvmsdk.conf %{buildroot}/etc/apache2/conf.d/

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)
%dir /etc/zvmsdk
%dir /var/log/zvmsdk
%dir /var/opt/zvmsdk
%dir /var/lib/zvmsdk
%config(noreplace) /var/opt/zvmsdk/zvmsdklogs
%config(noreplace) /etc/apache2/conf.d/zvmsdk.conf
%dir /etc/apache2
%dir /etc/apache2/conf.d
%dir /etc/sudoers.d
%dir /lib/systemd
%dir /lib/systemd/system

%post
/usr/bin/getent passwd zvmsdk >/dev/null || /usr/sbin/useradd -r -d /var/lib/zvmsdk -m -U zvmsdk -s /bin/bash 2>/dev/null 1>&2

chown zvmsdk /var/lib/zvmsdk/setupDisk
chgrp zvmsdk /var/lib/zvmsdk/setupDisk
chown -R zvmsdk:zvmsdk /etc/zvmsdk
chmod -R 755 /etc/zvmsdk
chown -R zvmsdk:zvmsdk /var/log/zvmsdk
chmod -R 755 /var/log/zvmsdk
chown -R zvmsdk:zvmsdk /var/opt/zvmsdk
chmod -R 755 /var/opt/zvmsdk
chown -R zvmsdk:zvmsdk /var/lib/zvmsdk
chmod -R 755 /var/lib/zvmsdk

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

if command -v firewall-cmd; then
  if [  "$(firewall-cmd --state)" = "running" ]; then
    echo "Firewalld is running, opening port 8080 in the docker zone"
    firewall-cmd --permanent --add-port=8080/tcp
    firewall-cmd --reload
  else
    echo "Firewalld is not running, not opening port 8080" >&2
  fi
else
  echo "Command firewall-cmd not found, not opening port 8080" >&2
fi

%postun
/usr/bin/getent passwd zvmsdk >/dev/null && userdel zvmsdk 2>/dev/null 1>&2
rm -fr /etc/logrotate.d/zvmsdklogs
