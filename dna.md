ISCSI ANSIBLE DNA

PACKAGE INSTALLATION

* Packages to Remove 
  * targetcli (ALL)
  * target (ALL)

* Repos
  * 45drives stable (ALL)
  * High-Availablility (CLUSTERED ONLY)
  * Ceph repos (CLUSTERED ONLY)

* Packages
  * pcs (CLUSTERED ONLY)
  * pacemaker (CLUSTERED ONLY)
  * corosync (CLUSTERED ONLY)
  * ceph-resource-agents (CLUSTERED ONLY)
  * scst-dkms scst-dkms-userspace scstadmin dkms (ALL, RHEL)
  * iscsi-scst scst-dkms scstadmin dkms (ALL, UBUNTU)

FIREWALL

* Services
  * high-availability (CLUSTERED ONLY)

* Ports
  * 3260/tcp (ALL)
  * 3260/udp (ALL)

KERNEL MODULES

* iscsi-scst (ALL)
* scst (ALL)
* scst_vdisk (ALL)


SYSTEMD SERVICES

* iscsi-scst.service (ALL)
[Unit]
Description=iSCSI SCST Target Daemon
Documentation=man:iscsi-scstd(8)
After=network.target
Before=scst.service
Conflicts=shutdown.target
[Service]
EnvironmentFile=-/etc/sysconfig/scst
PIDFile=/var/run/iscsi-scstd.pid
ExecStartPre=/sbin/modprobe iscsi-scst
ExecStart=/sbin/iscsi-scstd $ISCSID_OPTIONS
[Install]
WantedBy=multi-user.target

* pcsd (CLUSTERED ONLY)


CONFIG FILES

* /usr/lib/ocf/resource.d/heartbeat/iSCSITarget (CLUSTERED ONLY)
  * mitch user files
* /usr/lib/ocf/resource.d/heartbeat/iSCSILogicalUnit (CLUSTERED ONLY)
   * mitch user files 
* /etc/lvm/lvm.conf (CLUSTERED ONLY)
  * allow rbd
  * system_id_source "lvmlocal" 
* /etc/lvm/lvmlocal.conf (CLUSTERED ONLY)
  * system_id "iscsilun"


Planned File Structure
.
├── ansible.cfg
├── dna.md
├── group_vars
│   └── all.yml
├── iscsi-deploy.yml
├── library
├── LICENSE
├── Makefile
├── manual_process.md
├── packaging
├── plugins
│   └── lookup
│       └── ip.py
├── purge-iscsi.yml
├── README.md
├── roles
│   └── iscsi
│       ├── defaults
│       │   └── main.yml
│       ├── files
│       │   ├── iSCSILogicalUnit
│       │   ├── iscsi-scst.service
│       │   ├── iSCSITarget
│       │   └── lvm.conf
│       ├── tasks
│       │   ├── configure
│       │   │   ├── cluster.yml
│       │   │   ├── firewall.yml
│       │   │   ├── iscsi.yml
│       │   │   └── lvm_conf_mods.yml
│       │   ├── install
│       │   │   ├── main.yml
│       │   │   ├── repository.yml
│       │   │   ├── rhel.yml
│       │   │   └── ubuntu.yml
│       │   ├── main.yml
│       │   └── validate
│       │       ├── kernel_check.yml
│       │       └── main.yml
│       └── templates
└── testplan
