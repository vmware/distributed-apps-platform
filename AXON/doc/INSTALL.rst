.. contents::

***********
Environment
***********

For best performance, we recommend that your environment meets or exceeds the
os and hardware requirements. The following minimum requirements should support
a proof-of-concept environment with core axon services.

        *Workload Node (Windows) :   1 processor, 1GB memory, and 5 GB storage*

        *Workload Node (Linux) :     1 processor, 1 GB memory, and 5 GB storage*

As the number of workloads increase, so do the hardware requirements for the best performance.
By the addition of further services (Memory management etc.), hardware requirements might enhanced.
If performance degrades after enabling additional services or virtual machines,
consider adding hardware resources to your environment.

.. note::
    All the worklods must have minimum python version as 2.7.15

    For linux, we recommend a workload with *systemd*.

    For windows, *pywin32* python package must be installed.

    For remote installation for both the workloads openssh server must be installed.


********************************
Installation and Running Service
********************************
This consist of two steps -
    - Installation
    - Running service for validation-app-engine service

Local Installation
    * Ubuntu
    * Windows
    * Other Linux Distributions

Remote Installation

Local Installation
~~~~~~~~~~~~~~~~~~

===========================
Local Installation (Ubuntu)
===========================
#. Clone 'validation-app-engine' source code on an Ubuntu machine (Runner Machine) and install on Runner machine.

    python setup.py install

#. Create distributions (debian/sdist) using build.sh::

    $ ./build.sh**

    After running build.sh, it will create debian and sdist distributions in /var/lib/automation/packages directory. Along with this, this will create axon_requirements.txt in above directory.

    $ ls -lrt /var/lib/automation/packages
    * axon_service.tar.gz  -      *(Generated tarball)*
    * axon_service.deb     -      *(Debian package for validation-app-engine)*
    * axon_requirements.txt -     *(requirements.txt)*

#. Copy axon_requirements.txt and debian package to Ubuntu machine where you want to install this.
#. Now on Ubuntu machine, first install axon_requirements.txt using pip command and then install debian package::

    $ pip3 install -r axon_requirements.txt
    $ dpkg -i axon_service.deb

#. Check for installation in /opt directory in remote windows machine::

    $ ls -lrt /opt

#. Check if service is running::

    $ systemctl status axon_service

============================
Local Installation (Windows)
============================
Pre-requirement - (Python and OpenSSH server is installed on windows machine)

#. Repeat step 1-2 from the above.

#. Make sure pywin32 and python is installed on windows and following PATH is set in windows machine::

    $ pip install pywin32

#. To set this use this command on windows machine and then restart windows machine::

    > setx /M PATH "%PATH%;C:\Python27;C:\Python27\Scripts;C:\Python27\Lib\site-packages\pywin32_system32;C:\Python27\Lib\site-packages\win32"

#. Copy tarball created above (axon_service.tar.gz) to remote windows machine where you want to install this.

#. Now on Windows machine, install validation-app-engine using pip from power shell or command prompt::

    >  pip install axon_service.tar.gz

#. Register service to service manager from power shell or command prompt::

    > axon_service.exe --startup auto install

#. Start the service::

    > axon_service.exe start

==============================================
Local Installation (Other Linux Distributions)
==============================================
For other distributions, we don't have created distribution package i.e. rpm etc yet.
One can follow below instructions to run service there -

#. **Installation**::

    > python setup.py install

#. **Running the Service**

Upstart scripts (axon.service/axon_init.conf) are already created and put in 'validation-app-engine/etc'.
After successful installation, once can use these scripts to create run services in given workload.

        For systemd based workload use 'axon.service'.

        For init based workloads use 'axon_init.conf'.


Remote Installation
~~~~~~~~~~~~~~~~~~~
#. Follow steps 1-2 'Local Installation (Ubuntu)' for Linux based workloads and steps 1-3 from 'Local Installation (Windows)' for windows based workloads.
#. Copy below below python script on your local runner machine. Change user/password/ip etc and run::

    from axon.client.axon_installer import AxonRemoteOperationLinux, AxonRemoteOperationWindows
    # Gateway can be used if remote workload is accessible via a gateway machine
    gateway_host = '1.2.3.4'
    gw_user = 'gw_user'
    gw_password = 'gw_password'
    remote_ubuntu_machine = '1.2.3.5'
    remote_ubuntu_password = "changeit"
    remote_ubuntu_user = "ubuntu"
    remote_windows_machine = '1.2.3.6'
    remote_windows_password = "changeit"
    remote_windows_user = "Administrator"

    axn_linux = AxonRemoteOperationLinux(remote_ubuntu_machine,
                                         remote_user=remote_ubuntu_user,
                                         gw_host=gateway_host, gw_user='gw_user',
                                         gw_password='gw_password'
                                         remote_password=remote_ubuntu_password)

    axn_win = AxonRemoteOperationWindows(remote_windows_machine,
                                         remote_user='remote_windows_user,
                                         gw_host=gateway_host, gw_user='gw_user',
                                         gw_password='gw_password'
                                         remote_password=remote_windows_password)
    # Axon on linux Steps-
    # 1. copy and install requirements.txt
    requirement_file = '/var/lib/automation/packages/axon_requirements.txt'
    axn_linux.remote_install_requirements(requirement_file)

    # 2. Install axon on ubuntu machine using debian
    debian_file = '/var/lib/automation/packages/axon_service.deb'
    axn_linux.remote_install_distribution(debian_file)

    # Axon on windows Steps.
    # 1. install using sdist distribution package
    tarball_file = '/var/lib/automation/packages/axon_service.tar.gz'
    axn_win.remote_install_sdist(tarball_file)

    # 2. register service in service manager
    axn_win.remote_register_axon()

    # 3. start service
    axn_win.remote_start_axon()


.. note::
    If you want to set central DB (RIAK) to record and store traffic, you can do it in following way.

    **Linux**
        1. Add 'RIAK_PORT=<your riak port> in /etc/axon/axon.conf.
        2. restart axon_service

    **windows**
        1. Add RIAK_PORT as user data during windows boot up.
