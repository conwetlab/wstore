#!/bin/bash

# Define variables used in all scripts if not already set
if [[ -z "$WORKSPACE" ]]
  then
    export WORKSPACE=`pwd`
fi


# Check the system distribution
DIST=""

if [ -f "/etc/issue" ]; then
    # This file can exist in Debian and centos
    CONTENT=$(cat /etc/issue)

    if [[ $CONTENT == *CentOS* ]]; then
        DIST="rhel"
    elif [[ $CONTENT == *Ubuntu* || $CONTENT == *Debian* ]]; then
        DIST="deb"
    fi
elif [ -f "/etc/centos-release" ]; then
    DIST="rhel"
fi

# Install the different packages depending on the distribution
if [[ $DIST ==  "deb" ]]; then
    # Debian/Ubuntu
    echo "Debian/Ubuntu system"
    apt-get update
    apt-get install python python-pip
    apt-get install mongodb
    apt-get install wkhtmltopdf
    apt-get install xvfb
    # Install lxml dependencies
    apt-get install gcc
    apt-get install libxml2-dev libxslt1-dev zlib1g-dev python-dev

    # Install virtualenv
    pip install virtualenv
elif [[  $DIST == "rhel" ]]; then
    # CentOS 6
    echo "CentOS system. Note that only CentOS 6 is supported"
    ARCH=$(uname -m)

    # Install python 2.7 which is required
    # Install dependencies
    yum groupinstall "Development tools"

    yum install zlib-devel
    yum install bzip2-devel
    yum install openssl-devel
    yum install ncurses-devel

    # Download and compile python 2.7
    cd /opt
    wget --no-check-certificate https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz
    tar xf Python-2.7.6.tar.xz
    cd Python-2.7.6
    ./configure --prefix=/usr/local
    make && make altinstall

    # Install python 2.7 setup tools
    cd /opt
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
    sudo /usr/local/bin/python2.7 ez_setup.py
    sudo /usr/local/bin/easy_install-2.7 pip

    ln -s /usr/local/bin/python2.7 /usr/bin/python2.7
    ln -s /usr/local/bin/pip2.7 /usr/bin/pip2.7

    yum install libxml2-devel libxslt-devel python-devel

    # Install MongoDB repository
    if [[ $ARCH == "x86_64" ]]; then
        echo "[mongodb]
name=MongoDB Repository
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64/
gpgcheck=0
enabled=1" > /etc/yum.repos.d/mongodb.repo
    else
        echo "[mongodb]
name=MongoDB Repository
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/i686/
gpgcheck=0
enabled=1" > /etc/yum.repos.d/mongodb.repo
    fi

    yum install -y mongodb-org

    # Start mongodb
    service mongod start

    # Get wkhtmltopdf package download version 0.12.1
    if [[ $ARCH == "x86_64" ]]; then
        wget http://downloads.sourceforge.net/project/wkhtmltopdf/0.12.1/wkhtmltox-0.12.1_linux-centos6-amd64.rpm
        rpm -ivh wkhtmltox-0.12.1_linux-centos6-amd64.rpm
    else
        wget http://downloads.sourceforge.net/project/wkhtmltopdf/0.12.1/wkhtmltox-0.12.1_linux-centos6-i386.rpm
        rpm -ivh wkhtmltox-0.12.1_linux-centos6-i386.rpm
    fi

    yum install xorg-x11-server-Xvfb

    # Install virtualenv
    pip2.7 install virtualenv
    cd $WORKSPACE
else
    echo "Your system is not supported by this script" 1&>2
    exit 1
fi

